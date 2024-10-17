from django.urls import path
from . import views
from .views import index  , search_api_view


app_name = "search"
urlpatterns = [
    path("", index, name='index'),
    path('api/', search_api_view, name='search_api'),
    # path('', views.index, name='index')
    # path("", views.IndexView.as_view(), name="index"),
]   
