from .role_access import normalize_role, role_label, role_nav_items


def role_context(request):
    user = getattr(request, "user", None)
    return {
        "current_role": normalize_role(user),
        "current_role_label": role_label(user),
        "role_nav_items": role_nav_items(user),
    }
