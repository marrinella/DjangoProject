from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, DeleteView
from .models import Event
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import EventForm
from django.contrib.auth.forms import UserCreationForm
import calendar
from datetime import date
from collections import defaultdict
from django.contrib.auth.models import User
from .models import TelegramProfile
import random
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import TelegramProfile
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import TelegramProfile


class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "planner/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = date.today()

        year = self.request.GET.get("year")
        month = self.request.GET.get("month")
        if year and month:
            year = int(year)
            month = int(month)
        else:
            year = today.year
            month = today.month

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(year, month)

        start_day = month_days[0][0]
        end_day = month_days[-1][-1]

        month_events = (
            Event.objects.filter(
                user=self.request.user,
                date__range=(start_day, end_day),
            )
            .order_by("date", "time")
        )

        events_by_day = defaultdict(list)
        for e in month_events:
            events_by_day[e.date].append(e)

        prev_year = year
        prev_month = month - 1
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1

        next_year = year
        next_month = month + 1
        if next_month == 13:
            next_month = 1
            next_year += 1

        shown_date = date(year, month, 1)

        context["month_days"] = month_days
        context["events_by_day"] = dict(events_by_day)
        context["month_name"] = shown_date.strftime("%B")
        context["year"] = year
        context["month"] = month
        context["today"] = today
        context["prev_year"] = prev_year
        context["prev_month"] = prev_month
        context["next_year"] = next_year
        context["next_month"] = next_month
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "planner/event_form.html"
    success_url = reverse_lazy("event-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "planner/event_form.html"
    success_url = reverse_lazy("event-list")

    def get_queryset(self):
        return Event.objects.filter(user=self.request.user)

class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = "planner/event_confirm_delete.html"
    success_url = reverse_lazy("event-list")

    def get_queryset(self):
        return Event.objects.filter(user=self.request.user)

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        TelegramProfile.objects.create(user=self.object)
        return response

@login_required
def generate_link_code(request):
    if request.method != "POST":
        return redirect("telegram-link")

    profile, created = TelegramProfile.objects.get_or_create(user=request.user)

    code = str(random.randint(100000, 999999))
    profile.link_code = code
    profile.code_created_at = timezone.now()
    profile.save()

    return redirect("telegram-link")

@login_required
def unlink_telegram(request):
    if request.method != "POST":
        return redirect("telegram-link")

    profile, _ = TelegramProfile.objects.get_or_create(user=request.user)
    profile.telegram_id = None
    profile.link_code = None
    profile.save()
    return redirect("telegram-link")


class TelegramLinkView(LoginRequiredMixin, TemplateView):
    template_name = "planner/telegram_link.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, created = TelegramProfile.objects.get_or_create(user=self.request.user)
        context["profile"] = profile
        return context
