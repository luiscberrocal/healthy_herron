from django.urls import path

from . import views

app_name = "fasting"
urlpatterns = [
    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),
    # Start Fast
    path("start/", views.StartFastView.as_view(), name="start_fast"),
    # End Fast
    path("end/", views.EndFastView.as_view(), name="end_fast"),
    # HTMX endpoints
    path("timer-update/", views.timer_update_view, name="timer_update"),
    path("timer/", views.FastTimerView.as_view(), name="fast_timer"),
    # Fast detail/list views
    path("fasts/", views.FastListView.as_view(), name="fast_list"),
    path("fasts/<int:pk>/", views.FastDetailView.as_view(), name="fast_detail"),
    path("fasts/<int:pk>/edit/", views.FastUpdateView.as_view(), name="fast_update"),
    path("fasts/<int:pk>/delete/", views.FastDeleteView.as_view(), name="fast_delete"),
]
