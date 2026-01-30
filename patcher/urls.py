from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/compare/', views.CompareAPI.as_view(), name='api_compare'),
    path('api/patch/', views.PatchAPI.as_view(), name='api_patch'),
]
