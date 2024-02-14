import bcrypt
from cryptography.fernet import Fernet   
from cryptography.fernet import InvalidToken 
from rest_framework import status
from rest_framework.response import Response

# 성공, 실패
RESULT_SUCCSS = 'success'
RESULT_FAIL = 'fail'

# Result Code Define
RC_OK = 1
RC_OK_MSG = '정상처리 되었습니다.'

RC_BAD_ERROR = -1
RC_BAD_ERROR_MSG = '잘못된 요청입니다.'

RC_PASSWORD_ERROR = -2
RC_PASSWORD_ERROR_MSG = '비밀번호가 틀렸습니다.'

# 신청 상태
COMPLETED = 0
WAITING = 1
AVAILABLE = 2
UNAVAILABLE = -1

# 업로드 가능한 파일 확장자
ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'gif', 'png']

def encrypt_data(data, key):
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(data.encode('utf-8'))
    return encrypted_data   

def decrypt_data(encrypted_data, key):
    try:
        cipher = Fernet(key)        
        decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
        return decrypted_data
    except InvalidToken as e:
        print(f"InvalidToken Exception: {e}")
        return None  
    
def hash_password(password):
    # 비밀번호를 해시화하여 반환
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password

def verify_password(input_password, hashed_password):
    try: # 저장된 해시된 비밀번호와 사용자가 입력한 비밀번호를 비교
        return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password)
    except Exception as e:
        print(f"Exception: {e}")
        return None
    
