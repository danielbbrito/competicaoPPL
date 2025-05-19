from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('parte1/', views.parte1, name='parte1'),
    path('parte2/', views.parte2, name='parte2'),
    path('parte3/', views.parte3, name='parte3'),
]

