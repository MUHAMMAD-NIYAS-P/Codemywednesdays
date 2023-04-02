from django.urls import path
from .import views

urlpatterns = [
    path('<int:year>/<str:month>/', views.home, name="home")
]