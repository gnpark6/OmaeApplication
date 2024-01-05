import base64
import hashlib
import hmac
import json
import requests
import time
import logging


logger = logging.getLogger(__name__)


###
#
# 원본: https://github.com/NaverCloudPlatform/
#
class BaseAuthInfo:

    # Base Auth Info #

    # API Gateway api key
    api_key = ''
    # NCP Access key
    access_key = ''
    # NCP Access secret
    secret_key = ''

    # Cloud OutBound Mailer #
    # Outbound Mailer REST End-point
    mail_ep_url = 'https://mail.apigw.ntruss.com'
    mail_ep_uri = '/api/v1/mails'

    sms_ep_url = 'https://sens.apigw.ntruss.com'    # /sms/v2/services/{serviceId}/messages


    def __init__(self, api_key: str, access_key: str, secret_key: str) -> None:
        self.api_key = api_key
        self.access_key = access_key
        self.secret_key = secret_key


    def get_api_key(self):
        return self.api_key


    def get_mail_ep_path(self):
        return self.mail_ep_path


    def apigw_signature_v2(self, timestamp: int, uri: str):
        inputs = [ 'POST', ' ', uri, '\n' ]
        #inputs.append(str(timestamp))
        inputs.append(f"{timestamp}")
        inputs.append('\n')
        inputs.append(self.access_key)
        message = ''.join(inputs)

        hm = hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256)
        return base64.b64encode(hm.digest()).decode('utf-8')



class MailSender(BaseAuthInfo):

    def __init__(self, api_key, access_key, secret_key) -> None:
        super().__init__(api_key, access_key, secret_key)


    def request_sending(self, sender: str, title: str, body: str,
                        recipients: list, individual: bool, advertising: bool):
        try:
            '''
            mail_info = {
                "senderAddress": "omae@justpayments.co.kr",
                "title": "${customer_name}님 반갑습니다. ",
                "body": "귀하의 매장 '${store_name}'의 ${sale_date} 팩토링 준비가 완료되었습니다.",
                "recipients": [
                    {
                        "address": "mhshin71@gmail.com",
                        "name": "신길동",
                        "type": "R",
                        "parameters": {
                            "customer_name": "신길동",
                            "store_name": "성동 커피",
                            "sale_date": "2023년 12월 29일"
                        }
                    }
                ],
                "individual": True,
                "advertising": False
            }
            '''

            mail_info = {
                "senderAddress": sender,
                "title": title,
                "body": body,
                "recipients": recipients,
                "individual": individual,
                "advertising": advertising
            }

            timestamp = int(time.time() * 1000)
            apigw_signature = self.apigw_signature_v2(timestamp, self.mail_ep_uri)

            session = requests.Session()

            session.headers['x-ncp-apigw-timestamp'] = f"{timestamp}"
            session.headers['x-ncp-iam-access-key'] = self.access_key
            session.headers['x-ncp-apigw-signature-v1'] = apigw_signature
            session.headers['x-ncp-lang'] = 'ko-KR'
            session.headers['Content-Type'] = 'application/json'

            json_data = json.dumps(mail_info)

            url = self.mail_ep_url + self.mail_ep_uri
            resp = session.post(url=url, data=json_data.encode('utf-8'))
            if resp.status_code == 201:
                return 0

            return -(resp.status_code)

        except Exception as ex:
            logger.error(str(ex))
            return -20



class SMSSender(BaseAuthInfo):

    def __init__(self, access_key: str, secret_key: str, 
                 service_id: str, calling_number: str) -> None:
        super().__init__('', access_key, secret_key)
        self.service_id = service_id
        self.calling_number = calling_number


    def request_sending(self, countryCode: str, content: str, recipients: list):
        try:
            if countryCode != '82':
                return -10
            
            messages = []

            for recipient in recipients:
                msg = {
                    "to": recipient['to']
                }
                if 'content' in recipient:
                    msg['content'] = recipient['content']
                messages.append(msg)

            if len(messages) == 0:
                return -11

            body = {
                "type": 'SMS',
                "countryCode": countryCode,
                "from": self.calling_number,
                "content": content,
                "messages": messages
            }

            #if reserveTime is not None:
            #    body["reserveTime"] = reserveTime               # "yyyy-MM-dd HH:mm",
            #    if reserveTimeZone is not None:
            #        body["reserveTimeZone"] = reserveTimeZone   # TZ database name
            #    else:
            #        body["reserveTimeZone"] = "Asia/Seoul"

            timestamp = int(time.time() * 1000)
            sms_uri = f"/sms/v2/services/{self.service_id}/messages"

            apigw_signature = self.apigw_signature_v2(timestamp, sms_uri)

            session = requests.Session()

            session.headers['x-ncp-apigw-timestamp'] = f"{timestamp}"
            session.headers['x-ncp-iam-access-key'] = self.access_key
            session.headers['x-ncp-apigw-signature-v1'] = apigw_signature
            session.headers['Content-Type'] = 'application/json; charset=utf-8'

            url = self.sms_ep_url + sms_uri
            resp = session.post(url=url, json=body)

            if resp.status_code == 202:
                return 0

            return -(resp.status_code)

        except Exception as ex:
            logger.error(str(ex))
            return -20

