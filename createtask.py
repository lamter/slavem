import slavem
import json


settingPath = './conf/slavem_setting.json'
if __debug__:
    settingPath = './tmp/slavem_setting.json'

with open(settingPath, 'r') as f:
    kwarg = json.load(f)

monitor = slavem.Monitor(**kwarg)

tasksFile = './conf/tasks.json'
if __debug__:
    tasksFile = './tmp/tasks.json'

with open(tasksFile, 'r') as f:
    tasksArgs = json.load(f)
    # if __debug__:
    #     import datetime
    #     t = tasksArgs[0]
    #     now = datetime.datetime.now()
    #     now - datetime.timedelta(seconds=40)
    #     t['lanuch'] = now.time().strftime('%H:%M:%S')
    #     t['delay'] = 1

monitor.dbConnect()
monitor.db[monitor.taskCollectionName].remove({})

for taskKwargs in tasksArgs:
    monitor.createTask(**taskKwargs)

monitor.stop()
