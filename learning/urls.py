from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.profile_settings, name="profile_settings"),
    path("schedule/", views.schedule, name="schedule"),
    path("parents/", views.parent_dashboard, name="parent_dashboard"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),
    path("quizzes/<int:pk>/", views.take_quiz, name="take_quiz"),
    path("quiz-results/<int:pk>/", views.quiz_result, name="quiz_result"),
    path("words/<int:pk>/status/", views.update_word_status, name="update_word_status"),
    path("assignments/<int:pk>/submit/", views.submit_assignment, name="submit_assignment"),
    path("manage/", views.platform_admin_dashboard, name="platform_admin_dashboard"),
    path("manage/courses/", views.platform_admin_courses, name="platform_admin_courses"),
    path("manage/students/", views.platform_admin_students, name="platform_admin_students"),
    path("manage/submissions/", views.platform_admin_submissions, name="platform_admin_submissions"),
    path("manage/quizzes/", views.platform_admin_quizzes, name="platform_admin_quizzes"),
    path("manage/submissions/<int:pk>/", views.review_submission, name="review_submission"),
]
