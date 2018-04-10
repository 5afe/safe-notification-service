# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

app_name = "safe"

timestamp_regex = '\\d{4}[-]?\\d{1,2}[-]?\\d{1,2} \\d{1,2}:\\d{1,2}:\\d{1,2}'

urlpatterns = [
    url(r'^auth/$', views.AuthCreationView.as_view(), name='auth-creation')
]
