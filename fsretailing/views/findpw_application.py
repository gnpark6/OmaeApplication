import jwt
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.sessions.backends.db import SessionStore
from ..models.application_form import FindpwApplicationForm, ChangepwApplicationForm
from ..models.application import ApplicationDoc, Attachments
from library.def_common import *
from library.jwt_token import *
from common.ncloud_api import *

logger = logging.getLogger(__name__)

class NotexistError(Exception):
    pass

class CompareError(Exception):
    pass

class FindpwApplicationView(View):
    
    template = "stub/findpassword.html"
 
    def get(self, request):
        form = FindpwApplicationForm()
        context = {
            'form': form,
            'form_action': reverse('findpw-application')
        }
        return render(request, self.template, context)
    
    def post(self, request):
        try:
            form = FindpwApplicationForm(request.POST) 
            
            if form.is_valid():
                registration_no = form.cleaned_data['registration_no']
                phone = form.cleaned_data['phone']
                notification_method = form.cleaned_data['notification_method']
                        
            queryset = ApplicationDoc.objects.filter(registration_no=registration_no)
            
            if queryset:
                for item in queryset:
                    user_key = request.session.get(f'user_key_{registration_no}', None) 
                    print(type(item.phone), type(user_key))
                    decrypt_phone = decrypt_data(item.phone.encode('utf-8'), user_key)
                    print(type(decrypt_phone), decrypt_phone)
                    
                    if phone != decrypt_phone:
                        raise NotexistError
            else:    
                raise NotexistError
            
            print(notification_method)
            # mail_sender = MailSender('', settings.NC_ACCESS_KEY_ID, settings.NC_SECRET_KEY)
            # mail_sender.request_sending()
            
            request.session['registration_no'] = registration_no
            return redirect('changepw-application')   
        

        except NotexistError:
            messages.error(request, f"가입한 사업자가 없습니다.")
            return render(request, self.template)  
        
        except Exception as e:
            messages.error(request, f"잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.{e}")
            return render(request, self.template)
        
        
        
    def send_link_sms(self, phone: str):
        content = f'[오매] 비밀번호를 변경 링크 \n'
        recipients = {
            'to': phone
        }

        sms = SMSSender(settings.NC_ACCESS_KEY_ID, settings.NC_SECRET_KEY,
                        settings.NC_SMS_SERVICE_ID, settings.NC_SMS_CALLING_NUMBER)
        return sms.request_sending('82', content, [recipients])
    
class ChangepwApplicationView(View):
    template = "stub/changepassword.html"
    
    def get(self, request):
        
        form = ChangepwApplicationForm()
    
        # 세션 키로 세션 정보 가져옴
        registration_no = request.session.get('registration_no', '')
        
        print("change view")
        print(registration_no)
        
        context = {
            'form': form,
            'form_action': reverse('changepw-application')
        }
        return render(request, self.template, context)
    
    def post(self, request):
        form = ChangepwApplicationForm(request.POST, request.FILES)
        
        # 세션 키로 세션 정보 가져옴
        registration_no = request.session.get('registration_no', '')
        print(registration_no)
        try:
            if form.is_valid():
                password = form.cleaned_data['password']
                password_check = form.cleaned_data['password_check']
                
                if password != password_check:
                    raise CompareError
    
                hashed_password = hash_password(password)        
                
            queryset = ApplicationDoc.objects.filter(registration_no=registration_no)
            
            if queryset:
                for item in queryset:
                    item.password=hashed_password.decode('utf-8')
                    item.save()
               
        except CompareError:
            messages.error(request, "비밀번호가 일치하지 않습니다.")

        except Exception as e:
            messages.error(request, f"잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.{e}")
            
        context = {
            'form': form,
        }        

        return render(request, self.template, context) 