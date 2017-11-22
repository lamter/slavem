# coding:utf-8
import datetime
import logging
from dateutil.parser import parse
import pytz

import arrow

from .constant import LOCAL_TIMEZONE


class Task(object):
    """
    定时任务实例
    """

    DEALY_NOTICE_INTERVAL = datetime.timedelta(minutes=10)

    def __init__(self, name, type, lanuch, delay, host, des, active, tzinfo, weekday):
        # 需要保存到MongoDB的参数
        self.name = name
        self.type = type
        # self.lanuch = datetime.datetime.strptime(lanuch, '%H:%M:%S').time()
        self.lanuch = parse(lanuch).time()
        self.tzinfo = pytz.timezone(tzinfo)
        self.delay = delay  # min
        self.host = host
        self.des = des  # 备注描述
        self.active = active
        self.weekday = weekday
        # ====================
        self.toMongoDbArgs = ['name', 'type', 'lanuch', 'delay', 'host', 'des', 'active', 'tzinfo', 'weekday']

        self.log = logging.getLogger(u'{}'.format(self.name))
        self.log.parent = logging.getLogger('slavem')
        self.log.propagate = 1

        self.lanuchTime = arrow.now()
        self.deadline = arrow.now()
        self.refreshDeadline()
        # 最后一次延迟通知
        self.lastDelayNoticeTime = None

        self.isLate = False

    def toMongoDB(self):
        """
        生成用于保存到 MongoDB 的任务
        :return:
        """
        dic = {k: self.__dict__[k] for k in self.toMongoDbArgs}
        dic['lanuch'] = self.lanuch.strftime('%H:%M:%S')
        dic['tzinfo'] = self.tzinfo.zone
        return dic

    def __str__(self):
        s = super(Task, self).__str__()
        s.strip('>')
        s += ' '
        for k, v in self.__dict__.items():
            s += '{}:{} '.format(k, v)
        s += '>'
        return s

    def refreshDeadline(self):
        """
        截止时间
        :return:
        """
        now = arrow.now()
        # 当前的启动时间
        lanuchTime = datetime.datetime.combine(now.date(), self.lanuch)
        lanuchTime = self.tzinfo.localize(lanuchTime)
        self.log.info(u'当前的启动时间 {}'.format(lanuchTime))

        # 当前的截止时间
        deadline = lanuchTime + datetime.timedelta(seconds=60 * self.delay)
        self.log.info(u'当前的截止时间 {}'.format(lanuchTime))

        if deadline < now:
            # 现在已经过了今天的截止日期了，启动时间推迟到次日
            lanuchTime += datetime.timedelta(days=1)
            self.log.info(u'现在已经过了今天的截止日期了，启动时间推迟到次日 {}'.format(lanuchTime))

        while lanuchTime.isoweekday() not in self.weekday:
            # 对应的星期几,递增直到获得最终的下一个启动时间 launchTime
            lanuchTime += datetime.timedelta(days=1)
            self.log.info(u'lanuchTime 对应星期几 {}'.format(lanuchTime.isoweekday()))

        # 最终的计算得到的启动赶时间
        self.lanuchTime = lanuchTime
        # 从新计算截止时间
        self.deadline = lanuchTime + datetime.timedelta(seconds=60 * self.delay)

        self.lanuchTime = lanuchTime
        self.log.info(
            'name: {name} lanuch: {lanuch} lanuchTime: {lanuchTime} deadline: {deadline}'.format(**self.__dict__))

    # def getDeadline(self):
    #     now = arrow.now()
    #
    #     lanuchTime = datetime.datetime.combine(now.date(), self.lanuch)
    #     lanuchTime = self.tzinfo.localize(lanuchTime)
    #
    #     self.log.info('lanuchTime week: {}  self.weekday: {}'.format(lanuchTime.isoweekday(), str(self.weekday)))
    #     while lanuchTime.isoweekday() not in self.weekday:
    #         self.log.info('lanuchTime week: {}  self.weekday: {}'.format(lanuchTime.isoweekday(), str(self.weekday)))
    #         lanuchTime += datetime.timedelta(days=1)
    #
    #     deadline = lanuchTime + datetime.timedelta(seconds=60 * self.delay)
    #
    #     if deadline < now:
    #         # 现在已经过了截止日期了，时间推迟到次日
    #         deadline += datetime.timedelta(days=1)
    #
    #     return deadline

    def isReport(self, report):
        """
        检查是否是对应的 reposrt
        :param report:  dict()
        :return:
        """

        if self.name != report['name']:
            r, diff = False, 'name'
        elif self.type != report['type']:
            r, diff = False, 'type'
        elif self.host != report['host']:
            r, diff = False, 'host'
        elif self.lanuchTime > report['datetime'] or report['datetime'] > self.deadline:
            r, diff = False, 'datetime'
        else:
            r, diff = True, None

        if __debug__ and not r:
            rv = report[diff]
            sv = getattr(self, diff)
            self.log.debug(u'报告 {sv} 不匹配任务 {rv}'.format(sv=sv, rv=rv))

        return r

    def finishAndRefresh(self):
        """
        今天的任务完成了，刷新
        :return:
        """
        self.refreshDeadline()
        self.isLate = False

    def delayDeadline(self, seconds=60):
        """
        没有收到汇报,推迟 deadline
        :return:
        """
        self.deadline += datetime.timedelta(seconds=seconds)

    def setLate(self):
        self.isLate = True

    def toNotice(self):
        """

        :return:
        """
        return self.__dict__.copy()

    def toSameTaskKV(self):
        return {
            'name': self.name,
            'type': self.type,
            'lanuch': self.lanuch.strftime('%H:%M:%S'),
        }

    def __eq__(self, other):
        return self.toSameTaskKV() == other.toSameTaskKV()

    def isTimeToNoticeDelay(self):
        """
        是否到了报告延迟的时间
        :return:
        """
        if self.lastDelayNoticeTime is None:
            return True

        return arrow.now() - self.lastDelayNoticeTime > self.DEALY_NOTICE_INTERVAL

    def refreshLastDelayNoticeTime(self):
        """

        :return:
        """
        self.lastDelayNoticeTime = arrow.now()
