from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('parte1/', views.parte1, name='parte1'),
]

