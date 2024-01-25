import math
import re
from django import forms
from django.core.exceptions import ValidationError


NUMBER_ONLY = "this.value = this.value.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1');"


def validate_buzno(input: str):
    if len(input) != 10 or input.isnumeric() != True:
        return False
    
    sum = 0
    keys = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    for key, bzno in zip(keys, input):
        sum += (key * int(bzno))

    sum += math.floor((keys[8] * int(input[8])) / 10)
    remainder = (10 - (sum % 10)) % 10

    if int(input[9]) == remainder:
        return True

    return False


def validate_mobile_phone(value):
    if re.match(r'^010([0-9]{7,8})$', value) == None:
        raise ValidationError("핸드폰 번호 형식이 맞지 않음")


class StartApplicationForm(forms.Form):
    registration_no = forms.CharField(label="사업자등록번호",
                                      max_length=10,
                                      widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}))

    representative  = forms.CharField(label="대표자 이름",
                                      max_length=100)

    phone = forms.CharField(label="대표자 핸드폰 번호",
                            max_length=20,
                            widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}),
                            validators=[validate_mobile_phone])

    # def clean_registration_no(self):
    #     reg_no = self.cleaned_data.get("registration_no")
    #     if validate_buzno(reg_no) != True:
    #         raise ValidationError('올바르지 않은 사업자등록번호입니다.')

    #     self.registration_no = reg_no
    #     return self.registration_no
    

class TemporaryCodeForm(forms.Form):
    code = forms.CharField(label="인증번호",
                           max_length=6,
                           widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}))
    
    phone = forms.CharField(label="대표자 핸드폰 번호",
                            max_length=20,
                            widget=forms.TextInput(attrs={'readonly': True}),
                            validators=[validate_mobile_phone])

class UploadApplicationForm(forms.Form):
    registration_no = forms.CharField(label="사업자등록번호",
                                      max_length=10,
                                      widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}))
    
    phone = forms.CharField(label="대표자 핸드폰 번호",
                            max_length=200,
                            widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}),
                            validators=[validate_mobile_phone])    
    
    business_name = forms.CharField(label="가맹점 이름",
                                      max_length=160)

    representative  = forms.CharField(label="대표자 이름",
                                      max_length=200)

    email  = forms.CharField(label="이메일 주소",
                                      max_length=200)
    
    input_file = forms.FileField(label="사업자등록증:") 

    password = forms.CharField(label="비밀번호",
                                      max_length=200, widget=forms.PasswordInput(render_value=True))

    password_check = forms.CharField(label="비밀번호 확인",
                                      max_length=200, widget=forms.PasswordInput(render_value=True))

class ModifyApplicationForm(forms.Form):
    registration_no = forms.CharField(label="사업자등록번호",
                                      max_length=10,
                                      widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY, 'readonly': 'readonly', 'style': 'color: gray;'}))
    
    phone = forms.CharField(label="대표자 핸드폰 번호",
                            max_length=200,
                            widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY, 'readonly': 'readonly', 'style': 'color: gray;'}),
                            validators=[validate_mobile_phone])    
    
    business_name = forms.CharField(label="가맹점 이름",
                                      max_length=160)

    representative  = forms.CharField(label="대표자 이름",
                                      max_length=200)

    email  = forms.CharField(label="이메일 주소",
                                      max_length=200)
    
    input_file = forms.FileField(label="사업자등록증:") 
     
class LoginApplicationForm(forms.Form):
    registration_no = forms.CharField(label="사업자등록번호",
                                      max_length=10,
                                      widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}))
    
    phone = forms.CharField(label="대표자 핸드폰 번호",
                            max_length=200,
                            widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}),
                            validators=[validate_mobile_phone])
    
    password = forms.CharField(label="비밀번호",
                                      max_length=200, widget=forms.PasswordInput(render_value=True))        

SMS_EMAIL_CHOICES = [
    ('sms', 'SMS'),
    ('email', '이메일'),
]

class FindpwApplicationForm(forms.Form):
    registration_no = forms.CharField(label="사업자등록번호",
                                      max_length=10,
                                      widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}))
    
    phone = forms.CharField(label="대표자 핸드폰 번호",
                            max_length=200,
                            widget=forms.TextInput(attrs={'oninput': NUMBER_ONLY}),
                            validators=[validate_mobile_phone])

    notification_method = forms.ChoiceField(
        label="알림 수단",
        choices=SMS_EMAIL_CHOICES,
        widget=forms.RadioSelect
    ) 
    
class ChangepwApplicationForm(forms.Form):
    password = forms.CharField(label="비밀번호",
                                      max_length=200, widget=forms.PasswordInput(render_value=True))

    password_check = forms.CharField(label="비밀번호 확인",
                                      max_length=200, widget=forms.PasswordInput(render_value=True))