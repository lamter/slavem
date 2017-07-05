# slavem
监控全网其他服务的服务

## MongoDB
1. 配置一个MongoDB数据库，会创建数据库`slavem`。
2. 这个数据库用于接受定时任务的汇报和设置定时任务列表。
3. 为了你的人身安全，请设置用户名密码访问数据库。

## 配置文件
```json
{
  "host": "localhost",
  "port": 30020,
  "dbn": "slavem",
  "username": "slavem",
  "password": "slavem",
}
```


## 启动服务
```python
import slavem

monitor = slavem.Monitor(
    host='localhost',
    port=27017,
)
monitor.start()

```

## 任务
### 创建任务
```python

import slavem
import json

settingPath = './slavem_setting.json'
with open(settingPath, 'r') as f:
    kwarg = json.load(f)

monitor = slavem.Monitor(**kwarg)

taskKwargs = {
    'name': 'serverName', # 可以重复
    'type': 'serverType',
    'lanuch': '20:50:00', # 启动时刻
    'delay': 5,  # min 启动后 delay 分钟后查看启动结果
    'host': 'localhost', # 服务所在的 host
}

monitor.createTask(**taskKwargs)
monitor.stop()
```

### 查看任务
```python
import slavem
import json

settingPath = './slavem_setting.json'
with open(settingPath, 'r') as f:
    kwarg = json.load(f)

monitor = slavem.Monitor(**kwarg)
monitor.showTask()
monitor.stop()
```