# coding:utf-8
import json
import slavem

settingPath = './conf/slavem_setting.json'
with open(settingPath, 'r') as f:
    kwarg = json.load(f)

monitor = slavem.Monitor(**kwarg)
monitor.start()