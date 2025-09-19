from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('query/', views.query_domain, name='query_domain'),
    path('vazao_json/', views.vazao_json, name='vazao_json'),
]
