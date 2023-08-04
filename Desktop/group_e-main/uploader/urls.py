from django.urls import path
from . import views

app_name = 'uploader'

urlpatterns = [
    path('', views.ImageListView.as_view(), name='image_list'),
    path('image/create/', views.ImageCreateView.as_view(), name='image_create'),
]

