from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("parents/", views.parent_dashboard, name="parent_dashboard"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),
    path("assignments/<int:pk>/submit/", views.submit_assignment, name="submit_assignment"),
    path("manage/", views.platform_admin_dashboard, name="platform_admin_dashboard"),
    path("manage/courses/", views.platform_admin_courses, name="platform_admin_courses"),
    path("manage/students/", views.platform_admin_students, name="platform_admin_students"),
    path("manage/submissions/", views.platform_admin_submissions, name="platform_admin_submissions"),
    path("manage/submissions/<int:pk>/", views.review_submission, name="review_submission"),
]
