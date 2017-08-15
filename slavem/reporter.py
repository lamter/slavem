# coding:utf-8
import pymongo
import arrow
import datetime

from pymongo.errors import AutoReconnect

__all__ = [
    'Reporter'
]


class Reporter(object):
    """
    用于服务的汇报
    """

    def __init__(self, name, type, host, port, dbn, username, password,
                 localhost):
        self.name = name
        self.type = type
        self.host = host
        self.port = port
        self.dbn = dbn
        self.username = username
        self.password = password
        self.localhost = localhost

        # 链接数据库
        self.db = pymongo.MongoClient(self.host, self.port)[self.dbn]
        self.db.authenticate(self.username, self.password)

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
            'name': self.name,
            'type': self.type,
            'datetime': arrow.now().datetime,
            'host': self.localhost,
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
        try:
            heartbeat = self.db['heartbeat']
            filter = {
                'name': self.name,
                'type': self.type,
                'host': self.localhost,
            }
            r = {
                'name': self.name,
                'type': self.type,
                'datetime': arrow.now().datetime,
                'host': self.localhost,
            }

            heartbeat.find_one_and_replace(filter, r, upsert=True)
        except AutoReconnect:
            print('report 重连失败')


    def endHeartBeat(self):
        """
        停止心跳，在服务结束的时候要执行。否则服务器端会认为心跳异常
        :return:
        """
        heartbeat = self.db['heartbeat']
        filter = {
            'name': self.name,
            'type': self.type,
            'host': self.localhost,
        }
        heartbeat.delete_many(filter)
