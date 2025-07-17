#!/usr/bin/env python

import json
import subprocess
import time

while True:
    state = subprocess.getoutput('usbipd.exe state')
    state = json.loads(state)
    for device in state['Devices']:
        if device['BusId'] and device['InstanceId'] == 'USB\\VID_0403&PID_6014\\SC64XXXXXX':
            if device['ClientIPAddress'] is None:
                subprocess.call(('usbipd.exe', 'attach', '-b', device['BusId'], '-w'))
    time.sleep(0.25)
