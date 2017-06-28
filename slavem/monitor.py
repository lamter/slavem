# encoding:utf-8

import pymongo
import time
import tasks
import datetime
import requests

__all__ = [
    'Monitor'
]


class Monitor(object):
    """

    """

    def __init__(self, host='localhost', port=27017, dbn='slavem', username=None, password=None, serverChan=None):

        self.mongoSetting = {
            'host': host,
            'port': port,
            'dbn': dbn,
            'username': username,
            'password': password,
        }

        self.serverChan = serverChan or []
        if not self.serverChan:
            print(u'没有配置 serverChan 的密钥')

        # serverChan 的汇报地址
        self.serverChanFormat = "https://sc.ftqq.com/{SCKEY}.send?text={text}?desp={desp}"

        self.mongourl = 'mongodb://{username}:{password}@{host}:{port}/{dbn}?authMechanism=SCRAM-SHA-1'.format(
            **self.mongoSetting)

        self.__active = False

        # 下次查看是否已经完成任务的时间
        self.nextWatchTime = datetime.datetime.now()

        self.init()

    @property
    def db(self):
        return self.mongoclient[self.mongoSetting['dbn']]

    @property
    def taskCollectionName(self):
        return 'task'

    @property
    def reportCollectionName(self):
        return 'report'

    def dbConnect(self):
        """
        建立数据库链接
        :return:
        """
        try:
            # 检查链接是否正常
            self.mongoclient.server_info()
        except:
            # 重新链接
            if self.mongoSetting.get('username'):
                self.mongoclient = pymongo.MongoClient(self.mongourl)
            else:
                self.mongoclient = pymongo.MongoClient(
                    host=self.mongoSetting['host'],
                    port=self.mongoSetting['port']
                )

    def init(self):
        """
        初始化服务
        :return:
        """
        # 建立数据库链接
        self.dbConnect()

        # 从数据库加载任务
        self.loadTask()

        # 对任务进行排序
        self.sortTask()

    def _run(self):
        """

        :return:
        """
        while self.__active:
            # 阻塞等待直到下次任务时间
            self.watiWatchTime()

            # 检查任务
            self.checkTask()

            # 任务排序
            self.sortTask()

            # 最后更新任务时间
            self.refreshWatchTime()

    def watiWatchTime(self):
        """
        阻塞等待直到下次任务的时间
        :return:
        """
        now = datetime.datetime.now()
        if now < self.nextWatchTime:
            # 还没到观察下一个任务的时间
            rest = self.nextWatchTime - now
            time.sleep(rest.total_seconds())

    def start(self):
        """

        :return:
        """
        self._run()

    def stop(self):
        """

        :return:
        """
        try:
            self.mongoclient.close()
        except:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.mongoclient.close()
        except:
            pass

    def loadTask(self):
        """
        加载所有任务
        :return:
        """
        # 读取任务
        taskCol = self.db[self.taskCollectionName]
        taskList = []
        for t in taskCol.find():
            t.pop('_id')
            taskList.append(tasks.Task(**t))

        self.tasks = taskList

    def sortTask(self):
        """
        对任务进行排序
        :return:
        """
        self.tasks.sort(key=lambda x: x.deadline)

    def refreshWatchTime(self):
        """

        :return:
        """
        try:
            t = self.tasks[0]
            self.nextWatchTime = t.deadline
        except IndexError:
            # 如果没有任务，那么下次检查时间就是1分钟后
            self.nextWatchTime = datetime.datetime.now() + datetime.timedelta(seconds=60)
            return

    def checkTask(self):
        """
        有任务达到检查时间了，开始检查任务
        :return:
        """
        # 获取所有 deadline 时间到的任务实例
        taskList = []
        firstLanuchTime = None
        now = datetime.datetime.now()
        for t in self.tasks:
            assert isinstance(t, tasks.Task)
            if now >= t.deadline:
                taskList.append(t)
                try:
                    # 最早开始的一个任务
                    if firstLanuchTime < t.lanuchTime:
                        firstLanuchTime = t.lanuchTime
                except TypeError:
                    firstLanuchTime = t.lanuchTime

        # 读取定时任务汇报
        sql = {
            'datetime': {
                '$set': firstLanuchTime,
            }
        }

        reportCol = self.db[self.reportCollectionName]
        cursor = set(reportCol.find(sql))
        for report in cursor:
            for t in taskList:
                assert isinstance(t, tasks.Task)
                if t.isReport(report):
                    # 完成了，刷新deadline
                    if t.isLate:
                        # 迟到的汇报, 也需要发通知
                        self.noticeDealyReport(t, report)
                    t.finishAndRefresh()
                    taskList.remove(tasks)
                    break
            else:
                print('unknow report {}'.format(str(report)))

        for t in taskList:
            self.noticeUnreport(t)
            # 设置为启动迟到
            t.setLate()
            # 未完成，将 deadline 延迟到1分钟后
            t.delayDeadline()

    def noticeDealyReport(self, task, report):
        """

        :param task: tasks.Task
        :param report: dict()
        :return:
        """
        text = ''
        desp = ''
        # TODO 通知：任务延迟完成了
        self.sendServerChan(text, desp)

    def noticeUnreport(self, task):
        """
        :param task: tasks.Task
        :return:
        """
        # TODO 通知：未收到任务完成通知
        text = '服务{name}未启动'.format(name=task.name)
        desp = ''
        self.sendServerChan(text, desp)

    def sendServerChan(self, text, desp):
        """

        :return:
        """
        url = self.serverChanFormat.format(text=text, desp=desp)
        while True:
            r = requests.get(url)
            if r.status_code == 200:
                # 发送异常，重新发送
                time.sleep(10)
                break
