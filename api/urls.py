from django.urls import path
from . import views

urlpatterns = [
    path("search/", views.search_places, name="search_places"),
    path("search/area/", views.search_by_area, name="search_by_area"),
    path("categories/", views.get_categories, name="get_categories"),
    path("countries/", views.countries, name="countries"),
    path("locations/<str:country_code>/", views.locations, name="locations"),
    path("chat/", views.chat, name="chat"),
]