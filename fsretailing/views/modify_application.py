import jwt
import logging
import pytz
from library.jwt_token import *
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
from django.db import transaction
from ..models.application import ApplicationDoc, Attachments
from ..models.application_form import ModifyApplicationForm
from library.def_common import *

logger = logging.getLogger(__name__)

class ExtensionError(Exception):
    pass

class ModifyApplicationView(View):
    
    template = "stub/modify.html"

    def get(self, request):
        form = ModifyApplicationForm()
        
        registration_no = request.session.get('registration_no', '')
        phone = request.session.get('phone', '')
        business_name = request.session.get('business_name', '')
        representative = request.session.get('represnetative', '')
        email = request.session.get('email', '')

    # def get(self, request, session_key):
    #     form = ModifyApplicationForm()
        
    #     # 세션 키로 세션 정보 가져옴
    #     session = SessionStore(session_key)
    #     registration_no = session.get('registration_no', '')
    #     phone = session.get('phone', '')
    #     business_name = session.get('business_name', '')
    #     representative = session.get('represnetative', '')
    #     email = session.get('email', '')

        form = ModifyApplicationForm(initial={
            'registration_no': registration_no,
            'phone': phone,
            'business_name': business_name,
            'representative': representative,
            'email': email,
        })
        
        # print(f"modify_view")
        # print(f"{registration_no}", {decrypted_phone})
        # context = {
        #     'form': form,
        #     'form_action': reverse('modify-application', kwargs={'session_key': session_key}),
        # }
        context = {
            'form': form,
            'form_action': reverse('modify-application'),
        }

        return render(request, self.template, context) 
    
    # def post(self, request, session_key):
    def post(self, request):
        form = ModifyApplicationForm(request.POST, request.FILES)
        
        try:
            if form.is_valid():
                registration_no = form.cleaned_data['registration_no']
                phone = form.cleaned_data['phone']
                business_name = form.cleaned_data['business_name']
                representative = form.cleaned_data['representative']
                email = form.cleaned_data['email']
                input_file = request.FILES['input_file']
                
                extension=self.get_file_extension(input_file.name)
                print(type(extension))
                if not extension in ALLOWED_EXTENSIONS:
                    raise ExtensionError
                
                filedata = input_file.read()   
            
            print(f"{representative}, {email}")
            user_key = request.session.get(f'user_key_{registration_no}', None)     
            encrypted_representative = encrypt_data(representative, user_key)
            encrypted_email = encrypt_data(email, user_key)        
            
            print("")
            print("")
            print("")
                       
            # queryset = Attachments.objects.filter(filename=registration_no)
             
            # if queryset:
            #     for item in queryset:
            #         item.filedata=filedata
            #         item.extension=extension
            #         item.save()
                
                            
            # queryset = ApplicationDoc.objects.filter(registration_no=registration_no)
                    
            # if queryset:
            #     for item in queryset:
            #         item.business_name=business_name
            #         item.representative=encrypted_representative.decode('utf-8')
            #         item.email=encrypted_email.decode('utf-8')
            #         item.updated_at=datetime.now(pytz.utc)
            #         item.save()
            
            with transaction.atomic():                
                queryset = ApplicationDoc.objects.select_related('fileno').filter(registration_no=registration_no)
                
                if queryset:
                    for item in queryset:
                        item.fileno.filedata=filedata
                        item.fileno.extension=extension
                        item.fileno.save()
                        
                        item.business_name=business_name
                        item.representative=encrypted_representative.decode('utf-8')
                        item.email=encrypted_email.decode('utf-8')
                        item.updated_at=datetime.now(pytz.utc)
                        item.save()        
            
                    
        except ExtensionError:
            messages.error(request, "허용되지 않는 파일 형식입니다.")
            
        except Exception as e:
            messages.error(request, f"잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.{e}")

        context = {
            'form': form,
        }        

        return render(request, self.template, context)                            
        # return render(request, 'stub/success.html', context)

    def get_file_extension(self, filename):
        # 파일 이름에서 확장자 추출
        return filename.split('.')[-1].lower()
    
    def is_allowed_extension(self, filename):
        # 파일 확장자가 허용된 확장자 목록에 있는지 확인
        return self.get_file_extension(filename) in ALLOWED_EXTENSIONS