from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.static import serve


urlpatterns = [
    path("favicon.ico", serve, {"document_root": settings.BASE_DIR / "static" / "img", "path": "logo-chip-cutout.png"}),
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="learning/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("learning.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    urlpatterns = [
        re_path(r"^static/css/(?P<path>.*)$", serve, {"document_root": settings.BASE_DIR / "static" / "css"}),
        re_path(r"^static/img/(?P<path>.*)$", serve, {"document_root": settings.BASE_DIR / "static" / "img"}),
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ] + urlpatterns
    if not getattr(settings, "CLOUDINARY_STORAGE", None):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
