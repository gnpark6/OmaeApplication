from django.urls import path
from django.http import HttpResponse

from .views import start_application, upload_application, login_application, findpw_application, modify_application

urlpatterns = [
    path('', lambda request: HttpResponse('')),
    path('application/start/', start_application.StartApplicationView.as_view(), name='start-application'),
    path('application/tempcode/', start_application.TempCodeApplicationView.as_view(), name='tempcode-application'),
    path('application/upload/', upload_application.UploadApplicationView.as_view(), name='upload-application'),
    # path('application/modify/<str:session_key>/', modify_application.ModifyApplicationView.as_view(), name='modify-application'),
    path('application/modify/', modify_application.ModifyApplicationView.as_view(), name='modify-application'),
    path('application/login/', login_application.LoginApplicationView.as_view(), name='login-application'),  
    path('application/findpw/', findpw_application.FindpwApplicationView.as_view(), name='findpw-application'),  
    path('application/changepw/', findpw_application.ChangepwApplicationView.as_view(), name='changepw-application'),  
    # path('application/success/', upload_application.UploadApplicationView.success_page, name='success-page'),
]