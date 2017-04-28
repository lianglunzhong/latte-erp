# coding: utf-8
import sys
import requests
import hmac
import hashlib
import urllib
import pprint
import requests.packages.urllib3.util.ssl_
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'


app_key = "27760999"
app_pwd = "yuJC7DNDKQ"
code = '27d876bb-ccff-4488-aa72-d5f9d90260d3'

def get_link():
    url = 'http://authhz.alibaba.com/auth/authorize.htm?'

    data = [
        ('client_id', app_key),
        ('redirect_uri', 'localhost://test.php'),
        ('site', 'aliexpress'),
    ]

    si = ''
    for key, value in data:
        si += (key + value)
    signature = hmac.new(app_pwd, si, hashlib.sha1).digest().encode('hex').upper()

    para = urllib.urlencode(data)

    link = url + para + '&_aop_signature=' + signature

    print link

def get_token():
    redirect_uri = "localhost://test.php"
    url = "https://gw.api.alibaba.com/openapi/http/1/system.oauth2/getToken/{0}".format(app_key)

    data = [
        ("grant_type", "authorization_code"),
        ("need_refresh_token", "true"),
        ("client_id", app_key),
        ("client_secret", app_pwd),
        ("redirect_uri", urllib.quote_plus(redirect_uri)),
        ("code", code),
    ]

    r = requests.post(url, data=dict(data), timeout=5)

    result = r.json()
    pprint.pprint(result)


if __name__ == '__main__':
    if sys.argv[1] == 'link':
        get_link()
    if sys.argv[1] == 'token':
        get_token()