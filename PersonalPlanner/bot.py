from asgiref.sync import sync_to_async
import os
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PersonalPlanner.settings")

import django
django.setup()

from planner.models import TelegramProfile, Event
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import timedelta
from django.utils import timezone
import datetime
from zoneinfo import ZoneInfo


@sync_to_async
def get_profile_by_code(code: str) -> TelegramProfile:
    return TelegramProfile.objects.get(link_code=code)


@sync_to_async
def link_profile(profile: TelegramProfile, telegram_id: int) -> None:
    profile.telegram_id = telegram_id
    profile.link_code = None
    profile.save()


@sync_to_async
def get_events_for_5min_reminder():
    now = timezone.localtime(timezone.now())

    window_start = now + timedelta(minutes=4)
    window_end = now + timedelta(minutes=6)

    qs = (
        Event.objects
        .filter(
            reminded_5min_at__isnull=True,
            user__telegramprofile__telegram_id__isnull=False,
            date=window_start.date(),
            time__gte=window_start.time(),
            time__lt=window_end.time(),

        )
        .select_related("user", "user__telegramprofile")
        .order_by("time")
    )

    return list(qs)



@sync_to_async
def mark_5min_reminded(event_id: int):
    Event.objects.filter(id=event_id).update(reminded_5min_at=timezone.now())

async def reminder_5min_job(context):
    events = await get_events_for_5min_reminder()
    overdue_events = await get_overdue_5min_events()

    all_events = events + overdue_events
    seen_ids = set()

    for event in all_events:
        if event.id in seen_ids:
            continue
        seen_ids.add(event.id)

        telegram_id = event.user.telegramprofile.telegram_id

        text = (
            f"⏰ Нагадування!\n"
            f"🕒 {event.time.strftime('%H:%M')}\n"
            f"📌 {event.title}\n"
            f"⏳ (за 5 хвилин)"
        )

        if event.location:
            text += f"\n📍 {event.location}"

        await context.bot.send_message(chat_id=telegram_id, text=text)
        await mark_5min_reminded(event.id)




@sync_to_async
def get_overdue_5min_events():
    now = timezone.localtime(timezone.now())

    qs = (
        Event.objects
        .filter(
            reminded_5min_at__isnull=True,
            user__telegramprofile__telegram_id__isnull=False,
            date=now.date(),
            time__lt=(now + timedelta(minutes=5)).time(),
            time__gte=(now - timedelta(minutes=30)).time(),
        )
        .select_related("user", "user__telegramprofile")
        .order_by("time")
    )

    return list(qs)



@sync_to_async
def get_all_linked_profiles():
    return list(
        TelegramProfile.objects
        .filter(telegram_id__isnull=False)
        .select_related("user")
    )



@sync_to_async
def get_todays_events_for_user(user):
    today = timezone.localtime(timezone.now()).date()

    return list(
        Event.objects
        .filter(user=user, date=today)
        .order_by("time")
    )


async def daily_digest_job(context):
    profiles = await get_all_linked_profiles()

    for profile in profiles:
        events = await get_todays_events_for_user(profile.user)

        if not events:
            text = "🌅 Добрий ранок! Сьогодні у тебе немає запланованих справ 🙂"
        else:
            text = "🌅 Добрий ранок! Твої справи на сьогодні:\n\n"
            for e in events:
                text += f"🕒 {e.time.strftime('%H:%M')} — {e.title}\n"
                if e.location:
                    text += f"   📍 {e.location}\n"
                text += "\n"

        await context.bot.send_message(chat_id=profile.telegram_id, text=text)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Хелоу, я бот-нагадувач, на мені буде триматися твій тайм-менеджмент 🙂")



async def link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Використання: /link 123456")
        return

    code = context.args[0].strip()
    telegram_id = update.effective_user.id

    try:
        profile = await get_profile_by_code(code)
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text("❌ Код неправильний або вже використаний.")
        return

    await link_profile(profile, telegram_id)
    await update.message.reply_text("✅ Telegram успішно прив’язано!")



def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN env var")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))

    print("Bot is running...")
    app.job_queue.run_repeating(reminder_5min_job, interval=10, first=5)
    app.job_queue.run_daily(
        daily_digest_job,
        time=datetime.time(hour=5, minute=0, tzinfo=ZoneInfo("Europe/Kyiv"))
    )
    app.run_polling()



if __name__ == "__main__":
    main()


