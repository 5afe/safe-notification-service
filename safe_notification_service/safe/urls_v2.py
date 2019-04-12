from django.urls import path

from . import views_v2

app_name = "safe"

timestamp_regex = '\\d{4}[-]?\\d{1,2}[-]?\\d{1,2} \\d{1,2}:\\d{1,2}:\\d{1,2}'

urlpatterns = [
    path('auth/', views_v2.AuthCreationView.as_view(), name='auth-creation'),
]
