import jwt, base64, string, hashlib
from django.conf import settings
from rest_framework import status
from django.contrib import messages
from django.http import HttpResponse

class JwtToken(object):
    _salt = settings.JWT_SECRET_KEY
    _expire_message = dict(code=1200, msg="token: expired")
    _unknown_error_message = dict(code=4200, msg="token: invalid")

    _allowed_string = string.ascii_letters + string.digits
    _session_key_expired_in = 3600 * 3

    @classmethod
    def generate_token(cls, payload: dict) -> str:
        headers = dict(type="jwt", alg="HS256")
        result = jwt.encode(payload=payload, key=cls._salt, algorithm="HS256", headers=headers)
        return result


    @classmethod
    def parse_token(cls, token: str) -> tuple:
        verify_status = False

        try:
            payload_data = jwt.decode(token, cls._salt, algorithms=['HS256'])
            verify_status = True
        except jwt.ExpiredSignatureError:
            payload_data = cls._expire_message
        except Exception:
            payload_data = cls._unknown_error_message
        return verify_status, payload_data

def auth_check_jwt(function):
    def wrap(request, *args, **kwargs):
        token = request.COOKIES.get('OMAETOKEN', '')

        if token != None and token != '':
            ret, payload = JwtToken.parse_token(token)

            if ret != True:
                messages.error(request, "Invalid JWT Token")
                return HttpResponse(status=401)
                
            # request.user.tempcode = {
            #     "registration_no": payload['registration_no'],
            #     "representative": payload['representative']
            # }
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "Invalid JWT Token")
            return HttpResponse(status=401)
    return wrap