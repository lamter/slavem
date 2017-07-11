import datetime
import logging


class Task(object):
    """
    定时任务实例
    """

    def __init__(self, name, type, lanuch, delay, host, des):
        # 需要保存到MongoDB的参数
        self.name = name
        self.type = type
        self.lanuch = datetime.datetime.strptime(lanuch, '%H:%M:%S').time()
        self.delay = delay  # min
        self.host = host
        self.des = des  # 备注描述
        # ====================

        self.log = logging.getLogger('slavem')

        self.lanuchTime = datetime.datetime.now()
        self.deadline = datetime.datetime.now()
        self.refreshDeadline()

        self.isLate = False

    def toMongoDB(self):
        """
        生成用于保存到 MongoDB 的任务
        :return:
        """
        dic = {
            'name': self.name,
            'type': self.type,
            'lanuch': self.lanuch.strftime('%H:%M:%S'),
            'delay': self.delay,  # min
            'host': self.host,
            'des': self.des,
        }
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
        self.deadline = self.getDeadline()
        # 计算开始时间
        lanuchTime = datetime.datetime.combine(self.deadline.date(), self.lanuch)

        if lanuchTime > self.deadline:
            # 跨天了
            lanuchTime -= datetime.timedelta(days=1)

        self.lanuchTime = lanuchTime

    def getDeadline(self):
        """

        :return:
        """
        now = datetime.datetime.now()
        lanuchTime = datetime.datetime.combine(now.date(), self.lanuch)
        deadline = lanuchTime + datetime.timedelta(seconds=60 * self.delay)

        if deadline < now:
            # 现在已经过了截止日期了，时间推迟到次日
            deadline += datetime.timedelta(days=1)

        return deadline

    def isReport(self, report):
        """
        检查是否是对应的 reposrt
        :param report:  dict()
        :return:
        """
        if self.name != report['name']:
            return False
        if self.type != report['type']:
            return False
        if self.host != report['host']:
            return False
        if self.lanuchTime <= report['datetime'] <= self.deadline:
            return True
        else:
            return True

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
