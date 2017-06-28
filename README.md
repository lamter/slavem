# slavem
监控全网其他服务的服务

## 配置文件
```json
{
    ""
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
