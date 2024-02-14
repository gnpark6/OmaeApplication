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
from ..models.application import TemporaryCode, ApplicationDoc
from ..models.application_form import StartApplicationForm
from ..models.application_form import TemporaryCodeForm, UploadApplicationForm
from common.ncloud_api import SMSSender
from library.jwt_token import *
from library.def_common import *


logger = logging.getLogger(__name__)

class CompareError(Exception):
    pass

class StartApplicationView(View):

    template = "stub/form.html"

    duration_sec = 300


    def get(self, request):
        form = StartApplicationForm()
        context = {
            'form': form,
            'form_action': reverse('start-application')
        }
        return render(request, self.template, context)


    def post(self, request):
        form = StartApplicationForm(request.POST)

        try:
            if form.is_valid():
                registration_no = form.cleaned_data['registration_no']
                representative = form.cleaned_data['representative']
                phone = form.cleaned_data['phone']

                # 작성/검토 중인 사업자이면 로그인으로 이동
                user_key = request.session.get(f'user_key_{registration_no}', None)
                print(f"user_key:{user_key}")
                if user_key is not None:
                    if self.processing(request, user_key, registration_no, representative, phone) == True:
                            return redirect('/retailing/application/login/')
                    else:
                        raise CompareError
                
                # 인증코드 DB 저장
                code = self.save_tempcode(phone)
                
                # 인증코드 전송
                if self.send_sms(phone, code) == 0:
                    temp_form = TemporaryCodeForm()
                    temp_form.initial['phone'] = phone

                    context = {
                        'form': temp_form,
                        'form_action': reverse('tempcode-application'),
                        'counter_start': True,
                        'duration_sec': self.duration_sec - 10
                    }
                    
                    response = render(request, 'stub/upload.html', context)
                    
                    payload = {
                        "registration_no": registration_no,
                        "representative" : representative,
                        "phone": phone,
                    }
                    
                    # token = JwtToken.generate_token(payload=payload)
                    # response.set_cookie("OMAETOKEN", token)
                    # print(f"token:{token}")
                    
                    token = TemporaryToken.get_token(registration_no, representative)
                    response.set_cookie("OMAETOKEN", token)
                    return response

                else:
                    messages.error(request, "SMS전송 에러")
                    
        except CompareError:
            messages.error(request, "가입하신 사업자 번호가 있지만, 그 외 정보가 상이합니다.")
        except:
            messages.error(request, "잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.")

        context = {
            'form': form,
        }
        return render(request, self.template, context)
    

    def processing(self, request, user_key: str, registration_no: str, representative: str, phone: str):
        queryset = ApplicationDoc.objects.filter(registration_no=registration_no)
        if queryset:
            for item in queryset:
                decrypted_representative = decrypt_data(item.representative.encode('utf-8'), user_key)
                decrypted_phone = decrypt_data(item.phone.encode('utf-8'), user_key)
                if decrypted_representative != representative or decrypted_phone != phone:
                    return False
                else:
                    return True
              
        else:
            request.session.pop(f'user_key_{registration_no}', None)
            return False
        
        return False

    def save_tempcode(self, phone: str):
        nums = []
        for x in range(6):
            nums.append(str(randint(0, 9)))
        code = ''.join(nums)

        expired_at = datetime.now(pytz.utc) + timedelta(seconds=self.duration_sec)

        TemporaryCode.objects.create(
            phone=phone,
            code=code,
            expired_at=expired_at
        )
        return code


    def send_sms(self, phone: str, code: str):
        content = f'[오매] 인증번호: {code}\n타인 유출 주의'
        recipients = {
            'to': phone
        }

        sms = SMSSender(settings.NC_ACCESS_KEY_ID, settings.NC_SECRET_KEY,
                        settings.NC_SMS_SERVICE_ID, settings.NC_SMS_CALLING_NUMBER)
        return sms.request_sending('82', content, [recipients])


def require_temp_token():
    def _method_wrapper(function):
        def _arguments_wrapper(request, *args, **kwargs):
            temp_token = TemporaryToken.get_tempcode(request, "OMAETOKEN")
            if temp_token == None:
                messages.error(request, "잘못된 접근!")
                res = HttpResponseRedirect(reverse('start-application'))
                return res
            
            registration_no = temp_token["registration_no"]
            representative = temp_token["representative"]

            request.user.tempcode = {
                "registration_no": registration_no,
                "representative": representative
            }
            return function(request, *args, **kwargs)
        
        return _arguments_wrapper
    
    return _method_wrapper

# @method_decorator(auth_check_jwt, 'post')
@method_decorator(require_temp_token(), 'post')
class TempCodeApplicationView(View):
    def http_method_not_allowed(self, request, *args, **kwargs):
        messages.error(request, "잘못된 접근!")
        return HttpResponseRedirect(reverse('start-application'))


    def post(self, request, *args, **kwargs):
        form = TemporaryCodeForm(request.POST)

        try:
            tempcode = request.user.tempcode

            if tempcode['registration_no'] == '' or tempcode['representative'] == '':
                messages.error(request, "비정상 헤더")
                return HttpResponseRedirect(reverse('start-application'))

            if form.is_valid():
                registration_no = tempcode['registration_no']
                representative = tempcode['representative']
                
                print("temp views")
                print(registration_no, representative)
                code = form.cleaned_data['code']
                phone = form.cleaned_data['phone']

                retcode, remain_sec = self.verify_code(phone, code)

                if retcode == True:
                    # upload_form = UploadApplicationForm()                
                    # context = {
                    #     'form': upload_form,
                    #     'form_action': reverse('upload-application'),
                    #     'result': f"'{registration_no}' '{representative}'",
                    # }
                    # return render(request, 'stub/upload.html', context)
                    request.session['result'] = f"'{registration_no}' '{representative}'"
                    return redirect('upload-application')

                if remain_sec > 0:
                    messages.error(request, "인증코드가 잘못되었습니다.\n다시 시도해 주세요.")
                    context = {
                        'form': form,
                        'form_action': reverse('tempcode-application'),
                        'counter_start': True,
                        'duration_sec': remain_sec
                    }
                    return render(request, "stub/form.html", context)
                else:
                    messages.error(request, "인증코드가 만료되었습니다.\n다시 시도해 주세요.")
        except:
            messages.error(request, "잠시 후 다시 시도해 주세요.\n불편을 끼쳐드려 죄송합니다.")

        return HttpResponseRedirect(reverse('start-application'))


    def verify_code(self, phone, code):
        try:
            tc_qs = TemporaryCode.objects.filter(phone=phone).order_by('-pk')
            if tc_qs.exists():
                temp_code = tc_qs[0]
                now = datetime.now(pytz.utc)

                if now > temp_code.expired_at:
                    return False, 0

                if temp_code.code != code:
                    delta = temp_code.expired_at - now
                    return False, delta.seconds
                
                # 재사용 불가
                temp_code.expired_at = now
                temp_code.save()
                
                return True, 0
            
            else:
                return False, 0
        except:
            return False, 0



class TemporaryToken(object):

    secret = settings.JWT_SECRET_KEY

    @classmethod
    def get_token(cls, registration_no: str, representative: str, exp_sec: int = 120) -> str:
        expired_at = datetime.now(pytz.utc) + timedelta(seconds=exp_sec)
        payload = {
            "registration_no": registration_no,
            "representative": representative,
            "exp": expired_at,
        }
        return jwt.encode(payload=payload, key=cls.secret, algorithm="HS256")


    @classmethod
    def verify_token(cls, token: str) -> dict:
        try:
            options = {
                "require": ["registration_no", "representative"]
            }
            payload = jwt.decode(token, cls.secret, algorithms=['HS256'], options=options)
            payload["ret"] = 0
        except Exception as ex:
            payload = {
                "ret": -1,
                "error": str(ex)
            }
        
        return payload
    

    @classmethod
    def get_tempcode(cls, request, key) -> dict:
        token = request.COOKIES.get(key, '')
        if token == '':
            logger.info(f'Err: No Cookie {key}')
            return None

        payload = cls.verify_token(token)
        if payload["ret"] != 0:
            logger.info(f'Err: {payload["error"]}')
            return None
        
        logger.info(f'{payload["registration_no"]} {payload["representative"]}')
        tempcode = {
            "registration_no": payload["registration_no"],
            "representative": payload["representative"],
        }
        return tempcode

