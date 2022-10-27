import json
import os
import re
import sys
import time
import traceback
import requests
from time import sleep
from tkinter import messagebox


def printer(self, *args, sep=' ', end='\n', file=None, error=False, overwrite=False):
    if error:
        prefix = '\33[1;34;41m[SUDA_WIFI Checker]\33[0m \33[4;31m'
    else:
        prefix = '\33[1;34m[SUDA_WIFI Checker]\33[0m \33[4;34m'
    suffix = '\33[0m'
    if overwrite:
        print(f'\r{prefix}{self}{suffix}', *args, sep=sep, end=end, file=file)
    else:
        print(f'{prefix}{self}{suffix}', *args, sep=sep, end=end, file=file)


def error_msg_box(msg: str):
    printer('Error:', msg, error=True)
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


def ping(address: str) -> bool:
    if os.system(('ping -n 1 ' if sys.platform.startswith('win32') else 'ping -c1 ') + address) != 0:
        return not os.system(('ping -n 3 ' if sys.platform.startswith('win32') else 'ping -c3 ') + address)
    return True


def ipconfig() -> str:
    return os.popen('ipconfig' if sys.platform.startswith('win32') else 'ifconfig').read()


def check_wlan_ssid(ssid_prefix: str) -> bool:
    if sys.platform.startswith('darwin'):
        wifi_info = os.popen('/System/Library/PrivateFrameworks/Apple80211.framework/Versions/A/Resources/airport -I').read()
        ssid_match = re.search(r'\s*SSID\s*: (.+)\s*', wifi_info)
        if not ssid_match or len(ssid_match.groups()) < 1:
            return False
        ssid = ssid_match.group(1)
        return ssid.startswith(ssid_prefix)
    if sys.platform.startswith('win32'):
        wifi_info = os.popen('netsh wlan show interfaces').read()
        ssid_match = re.search(r'\s*SSID: (.+)\s*', wifi_info).group(1)
        if not ssid_match or len(ssid_match.groups()) < 1:
            return False
        ssid = ssid_match.group(1)
        return ssid.startswith(ssid_prefix)
    return True


def retry_interval(seconds: int, msg: str = 'Retry'):
    if seconds <= 0:
        return
    while seconds:
        printer(f'{msg} after waiting {seconds} second(s)... ', end='', overwrite=True)
        sleep(1)
        seconds -= 1
    printer(f'\n{msg}...', overwrite=True)


def main_loop():
    retry_times = 0
    while 1:
        if not check_wlan_ssid('SUDA-WIFI') and not check_wlan_ssid('SUDA_WIFI'):
            printer('Not in the Campus network environment (SUDA_WIFI).')
            retry_times = 0
            retry_interval(10, 'Continue check')
            continue
        if ping('www.baidu.com'):
            printer('Successful Internet connection.')
            retry_times = 0
            retry_interval(10, 'Continue check')
            continue
        if not ping('10.9.1.3'):
            printer('It seems that something is wrong with the campus network (SUDA_WIFI), process is abandoned.',
                    error=True)
            retry_interval(10)
            continue
        printer('Process start.')
        IP = re.findall(r'10\d?\.\d{1,3}\.\d{1,3}\.\d{1,3}', ipconfig())
        if len(IP) < 1:
            printer('Can not get IP address, retry 3 seconds later.')
            retry_interval(3)
            continue
        printer('Get IP address：', IP)
        try:
            printer('Login...')
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
            printer('Login failed, retry 5 seconds later.')
            traceback.print_exc()
            retry_times += 1
            retry_interval(5)
        else:
            responses.encoding = "utf-8"
            response = json.loads(responses.text[1:-1])
            printer('responses: ', response)
            if response['result'] == '1':
                printer('Login successes.')
                retry_times = 0
                retry_interval(10, 'Continue check')
                continue
            if retry_times >= 5:
                error_msg_box('Login failed (response code error) 5 more times, Check if your IP address is in the'
                              ' first of list: {ip}, if not, modify the "index" property in the JSON file with'
                              ' the index of your IP in the list: {ip} (starting from 0).\n'
                              'Process will exit.'.format(ip=IP))
                exit(4)
            printer('Login failed (response code error), retry 3 seconds later.')
            retry_times += 1
            retry_interval(3)


if __name__ == '__main__':
    main_loop()
