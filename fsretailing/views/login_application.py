import logging
import pytz
import os 
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
from ..models.application_form import LoginApplicationForm
from ..models.application import ApplicationDoc, Attachments
from library.def_common import encrypt_data, decrypt_data, verify_password
from cryptography.fernet import Fernet
from library.jwt_token import *

logger = logging.getLogger(__name__)

class NotexistError(Exception):
    pass

class PhonenumberError(Exception):
    pass

class PasswordError(Exception):
    pass

class LoginApplicationView(View):
    
    template = "stub/login.html"
 
    def get(self, request):
        form = LoginApplicationForm()
        context = {
            'form': form,
            'form_action': reverse('login-application')
        }
        return render(request, self.template, context)
    
    def post(self, request):
        try:
            form = LoginApplicationForm(request.POST)   
            if form.is_valid():
                registration_no = form.cleaned_data['registration_no']
                phone = form.cleaned_data['phone']
                password = form.cleaned_data['password']
                        
            queryset = ApplicationDoc.objects.select_related('fileno').filter(registration_no=registration_no)
                    
            if queryset:
                for item in queryset:
                    user_key = request.session.get(f'user_key_{registration_no}', None)               
                    decrypted_phone = decrypt_data(item.phone.encode('utf-8'), user_key)
                    if phone != decrypted_phone:
                        raise PhonenumberError
                        
                    decrypted_representative = decrypt_data(item.representative.encode('utf-8'), user_key)      
                    decrypted_email = decrypt_data(item.email.encode('utf-8'), user_key) 
                    registration_no = item.registration_no
                    business_name = item.business_name
                    status = item.status
                    file_data = item.fileno.filedata
                    filename = item.fileno.filename + "." + item.fileno.extension
                    
                    if verify_password(password, item.password.encode('utf-8')) == False:
                        raise PasswordError
                                       
            else:
                raise NotexistError
                # return render(request, 'stub/notfound.html')     


            if status == "2" or status == "-1":
                # queryset = Attachments.objects.filter(filename=registration_no)
                
                # if queryset:
                #     for item in queryset:
                #         file_data = item.filedata
                #         print(type(file_data))

                # filename = item.filename + "." + item.extension
                output_path = os.path.join("C:\\Users\\ruin9\\temp", filename)  

                # 파일 저장
                with open(output_path, "wb") as file:
                    file.write(file_data)
                    
                context = {
                    'registration_no' : registration_no,
                    'phone' : decrypted_phone,
                    'business_name' : business_name,
                    'representative' : decrypted_representative,
                    'email' : decrypted_email,
                    'status' : status,
                    'filepath' : output_path
                }
                
                
                return render(request, 'stub/result.html', context)

            else:
                request.session['registration_no'] = registration_no
                request.session['phone'] = decrypted_phone
                request.session['business_name'] = business_name
                request.session['representative'] = decrypted_representative
                request.session['email'] = decrypted_email
                # return redirect('modify-application', session_key=request.session.session_key)
                return redirect('modify-application')
            
        except NotexistError:
            messages.error(request, f"가입한 사업자가 없습니다.")
            return render(request, self.template)   
        
        except PhonenumberError:
            messages.error(request, f"등록된 사업자 번호와 핸드폰 번호가 일치하지 않습니다.")   
            return render(request, self.template)
                
        except PasswordError:
            messages.error(request, f"패스워드가 일치하지 않습니다.")   
            return render(request, self.template)
                        
        except Exception as e:
            messages.error(request, f"잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.{e}")
            return render(request, self.template)
                    