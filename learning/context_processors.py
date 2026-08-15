def user_role(request):
    if not request.user.is_authenticated:
        return {"user_role": ""}
    return {"user_role": getattr(getattr(request.user, "profile", None), "role", "")}
