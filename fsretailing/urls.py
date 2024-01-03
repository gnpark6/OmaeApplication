from django.urls import path
from django.http import HttpResponse

from .views import start_application


urlpatterns = [
    path('', lambda request: HttpResponse('')),
    path('application/start/', start_application.StartApplicationView.as_view(), name='start-application'),
    path('application/tempcode/', start_application.TempCodeApplicationView.as_view(), name='tempcode-application'),
]