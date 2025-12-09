from django.urls import path

from . import views

urlpatterns = [
    path("", views.calculator_view, name="calculator"),
    path("profiles/", views.profile_list, name="profile_list"),
    path("weapons/", views.weapon_list, name="weapon_list"),
    path("keywords/", views.keyword_list, name="keyword_list"),
]
