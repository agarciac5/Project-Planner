import hashlib

from django.conf import settings
from django.core.cache import cache


def _login_keys(request, email):
    normalized_email = str(email or "").strip().lower()
    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    digest = hashlib.sha256(
        f"{normalized_email}|{ip_address}".encode("utf-8")
    ).hexdigest()
    email_digest = hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
    return (
        f"login-attempt:pair:{digest}",
        f"login-attempt:email:{email_digest}",
    )


def login_is_blocked(request, email):
    maximum = settings.LOGIN_MAX_ATTEMPTS
    return any(
        int(cache.get(key, 0)) >= maximum
        for key in _login_keys(request, email)
    )


def record_failed_login(request, email):
    timeout = settings.LOGIN_LOCKOUT_SECONDS
    for key in _login_keys(request, email):
        cache.set(key, int(cache.get(key, 0)) + 1, timeout)


def clear_failed_logins(request, email):
    cache.delete_many(_login_keys(request, email))
