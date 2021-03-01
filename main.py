import json
import os
import re
import sys
import traceback
from time import sleep
from tkinter import messagebox

try:
    import requests
except ModuleNotFoundError:
    os.system(sys.executable + ' -m pip install requests')
    import requests


def error_msg_box(msg: str):
    print('Error:', msg)
    messagebox.showerror(title='Error', message=msg)


with open('config.json', 'r', encoding='utf-8') as cfg:
    _cfg_json = json.load(cfg)
    STUDENT_ID = _cfg_json['student_id']
    _LOGIN_TYPE = _cfg_json['type']
    PASSWORD = _cfg_json['password']
    IP_INDEX = _cfg_json['index']

if _LOGIN_TYPE == 0:
    LOGIN_TYPE = ''
elif _LOGIN_TYPE == 1:
    LOGIN_TYPE = '@zgyd'
else:
    error_msg_box('unsupported login type in config.json')
    exit(1)

if sys.platform.startswith('linux') and os.system('ifconfig'):
    error_msg_box('\nCommand \'ifconfig\' not found, but can be installed with:\n'
                  'sudo apt install net-tools      # Ubuntu (Debian)\n'
                  'sudo yum install net-tools      # CentOS (Red Hat)\n')
    exit(2)


def ping(address):
    return not os.system(('ping -n 3 ' if sys.platform.startswith('win32') else 'ping -c3 ') + address)


def ipconfig() -> str:
    return os.popen('ipconfig' if sys.platform.startswith('win32') else 'ifconfig').read()


def main_loop():
    retry_times = 0
    while 1:
        if ping('www.baidu.com'):
            print('Successful Internet connection.\n')
            sleep(10)
            continue
        if not ping('a.suda.edu.cn'):
            print('Not in the Campus network environment (SUDA_WIFI), process is abandoned.\n')
            sleep(10)
            continue
        print('Process start.')
        IP = re.findall(r'10\d?\.\d{1,3}\.\d{1,3}\.\d{1,3}', ipconfig())
        if len(IP) < 1:
            print('Can not get IP address, retry 3 seconds later.')
            sleep(3)
            continue
        print('Get IP address：', IP)
        try:
            print('Login...')
            responses = requests.get(url='http://10.9.1.3:801/eportal/',
                                     params=dict(a='login',
                                                 c="Portal",
                                                 wlan_user_ip=IP[IP_INDEX],
                                                 user_password=PASSWORD,
                                                 user_account=",0,{}{}".format(STUDENT_ID, LOGIN_TYPE),
                                                 login_method=1),
                                     timeout=1)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            if retry_times >= 5:
                error_msg_box('Login failed 5 more times, check the configuration in the JSON file please.\n'
                              'Process will exit.')
                exit(3)
            print('Login failed, retry 5 seconds later.')
            traceback.print_exc()
            retry_times += 1
            sleep(5)
        else:
            responses.encoding = "utf-8"
            response = json.loads(responses.text[1:-1])
            print('responses: ', response)
            if response['result'] == '1':
                print('Login successes.')
                retry_times = 0
                sleep(10)
                continue
            if retry_times >= 5:
                error_msg_box('Login failed (response code error) 5 more times, Check if your IP address is in the'
                              ' first of list: {ip}, if not, modify the "index" property in the JSON file with'
                              ' the index of your IP in the list: {ip} (starting from 0).\n'
                              'Process will exit.'.format(ip=IP))
                exit(4)
            print('Login failed (response code error), retry 2 seconds later.')
            retry_times += 1
            sleep(2)


if __name__ == '__main__':
    main_loop()
