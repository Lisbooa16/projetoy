from django.urls import path

from . import views

app_name = "mailbox"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("compose/", views.compose, name="compose"),
    path("thread/<int:thread_id>/", views.thread_detail, name="thread_detail"),
]
