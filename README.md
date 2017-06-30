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
  "port": 27017,
  "dbn": "slavem",
  "serverChan": [
    "SCU3933Tab181d054223a5d94711915b357cd8c5582e9d81cbc5b"
  ]
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
