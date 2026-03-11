from django.urls import path
from .views import dashboard, login_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path("", dashboard, name="home"),
]