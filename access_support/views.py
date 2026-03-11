from django.shortcuts import render, redirect
from django.contrib.auth import login
from .login import EmailLoginForm


def dashboard(request):
    return render(request, "dashboard/dashboard.html")


def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = EmailLoginForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)

            return redirect("home")

    else:
        form = EmailLoginForm()

    return render(request, "access_support/login.html", {"form": form})