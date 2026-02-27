from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views import View

from .forms import RegistrationForm


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "users/register.html", {"form": RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
        return render(request, "users/register.html", {"form": form})


class UserLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "users/login.html")

    def post(self, request):
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next", "/dashboard/")
            return redirect(next_url)
        return render(
            request,
            "users/login.html",
            {"error": "Invalid email or password.", "email": email},
        )


class UserLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("login")
