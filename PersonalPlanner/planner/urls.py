from django.urls import path
from django.contrib.auth import views as auth_views
from .views import EventListView, EventCreateView, EventUpdateView, EventDeleteView, SignUpView
from .views import TelegramLinkView, generate_link_code, unlink_telegram




urlpatterns = [
    path('', EventListView.as_view(), name='event-list'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("events/new/", EventCreateView.as_view(), name="event-create"),
    path("events/<int:pk>/edit/", EventUpdateView.as_view(), name="event-edit"),
    path("events/<int:pk>/delete/", EventDeleteView.as_view(), name="event-delete"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("telegram/", TelegramLinkView.as_view(), name="telegram-link"),
    path("telegram/generate/", generate_link_code, name="telegram-generate"),
    path("telegram/unlink/", unlink_telegram, name="telegram-unlink"),


]
