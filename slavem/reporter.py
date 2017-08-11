import pymongo
import arrow
import datetime

__all__ = [
    'Reporter'
]


class Reporter(object):
    """
    用于服务的汇报
    """

    def __init__(self, slavemName, slavemType, slavemHost, slavemPort, slavemdbn, slavemUsername, slavemPassword,
                 slaveMLocalhost):
        self.slavemName = slavemName
        self.slavemType = slavemType
        self.slavemHost = slavemHost
        self.slavemPort = slavemPort
        self.slavemdbn = slavemdbn
        self.slavemUsername = slavemUsername
        self.slavemPassword = slavemPassword
        self.slaveMLocalhost = slaveMLocalhost

        # 链接数据库
        self.db = pymongo.MongoClient(self.slavemHost, self.slavemPort)[self.slavemdbn]
        self.db.authenticate(self.slavemUsername, self.slavemPassword)

        # 是否已经启动汇报过了
        self.isStartReported = False

        # 心跳最少要5秒
        self.heartBeatMinInterval = datetime.timedelta(seconds=5)

    def lanuchReport(self):
        """
        启动时的汇报
        :return:
        """
        if self.isStartReported:
            return
        self.isStartReported = True

        # 提交报告的 collection
        report = self.db['report']
        r = {
            'name': self.slavemName,
            'type': self.slavemType,
            'datetime': arrow.now().datetime,
            'host': self.slaveMLocalhost,
        }

        r = report.insert_one(r)

        if not r.acknowledged:
            print(u'启动汇报失败!')
        else:
            print(u'启动汇报完成')

    def heartBeat(self):
        """
        服务的心跳，建议19秒次。服务器端为每分钟检查一次心跳，可以保证1分钟有3次心跳
        :return:
        """
        heartbeat = self.db['heartbeat']
        filter = {
            'name': self.slavemName,
            'type': self.slavemType,
            'host': self.slaveMLocalhost,
        }
        r = {
            'name': self.slavemName,
            'type': self.slavemType,
            'datetime': arrow.now().datetime,
            'host': self.slaveMLocalhost,
        }

        heartbeat.find_one_and_replace(filter, r, upsert=True)

    def endHeartBeat(self):
        """
        停止心跳，在服务结束的时候要执行。否则服务器端会认为心跳异常
        :return:
        """
        heartbeat = self.db['heartbeat']
        filter = {
            'name': self.slavemName,
            'type': self.slavemType,
            'host': self.slaveMLocalhost,
        }
        heartbeat.delete_many(filter)
