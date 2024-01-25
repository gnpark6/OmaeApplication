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
from random import randint
from ..models.application import ApplicationDoc, Attachments
from ..models.application_form import UploadApplicationForm
from common.ncloud_api import SMSSender
from cryptography.fernet import Fernet
from library.def_common import *
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class ExtensionError(Exception):
    pass

class CompareError(Exception):
    pass

class UploadApplicationView(View):
    template = "stub/upload.html"
    
    def get(self, request):
        form = UploadApplicationForm()
        # result = request.session.get('result', None)
        # print(result, type(result))
        
        try:
            registration_no = request.session.get('registration_no', '')
            representative = request.session.get('representative', '')
            print(f"result : {registration_no} {representative}")
            
            form = UploadApplicationForm(initial={
                'registration_no': registration_no,
                'representative': representative,
            })
            
            context = {
                'form': form,
                'form_action': reverse('upload-application')
            }
            return render(request, self.template, context)    
                
        except Exception:
            return HttpResponse("잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.")
        # context = {
        #     'form': form,
        #     'form_action': reverse('upload-application')
        # }
        # return render(request, self.template, context)
    
    def post(self, request):
        form = UploadApplicationForm(request.POST, request.FILES)
        
        try:
            if form.is_valid():
                registration_no = form.cleaned_data['registration_no']
                phone = form.cleaned_data['phone']
                business_name = form.cleaned_data['business_name']
                representative = form.cleaned_data['representative']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                password_check = form.cleaned_data['password_check']
                    
                if password != password_check:
                    raise CompareError
    
                input_file = request.FILES['input_file']
                
                # print(f"File Extension: {self.get_file_extension(input_file.name)}")
                
                # if not self.is_allowed_extension(input_file.name):
                #     raise VaildationError
                
                extension=self.get_file_extension(input_file.name)
                
                if not extension in ALLOWED_EXTENSIONS:
                    raise ExtensionError
                
                filedata = input_file.read()                
                
            attachments = Attachments.objects.create(
                filename=registration_no,
                filedata=filedata,
                extension=extension
            )
            
            user_key = Fernet.generate_key()
            # request.session[f'user_key_{registration_no}'] = user_key
            request.session[f'user_key_{registration_no}'] = user_key.decode('utf-8')
            
            encrypted_representative = encrypt_data(representative, user_key)
            encrypted_phone = encrypt_data(phone, user_key)
            encrypted_email = encrypt_data(email, user_key)
            hashed_password = hash_password(password)
            
            KST = pytz.timezone('Asia/Seoul')
            
            ApplicationDoc.objects.create(
                fileno=attachments,
                registration_no=registration_no,
                business_name=business_name,
                representative=encrypted_representative.decode('utf-8'),
                phone=encrypted_phone.decode('utf-8'),
                email=encrypted_email.decode('utf-8'),
                password=hashed_password.decode('utf-8'),
                created_at=datetime.now(KST),
                updated_at=datetime.now(KST),
                status=COMPLETED
            )
        
        except CompareError:
            messages.error(request, "비밀번호가 일치하지 않습니다.")
    
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
    