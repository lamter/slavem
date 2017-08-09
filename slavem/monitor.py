import sys
import signal
import logging.config
import time
import traceback

import pymongo
import datetime
import requests
import log4mongo.handlers

from .tasks import Task

__all__ = [
    'Monitor'
]
a = 0


class Monitor(object):
    """

    """
    name = 'slavem'

    def __init__(self, host='localhost', port=27017, dbn='slavem', username=None, password=None, serverChan=None,
                 loggingconf=None):
        """
        :param host:
        :param port:
        :param dbn:
        :param username:
        :param password:
        :param serverChan:
        :param loggingconf: logging 的配置 Dict()
        """

        self.mongoSetting = {
            'host': host,
            'port': port,
            'dbn': dbn,
            'username': username,
            'password': password,
        }

        self.log = logging.getLogger()
        self.initLog(loggingconf)

        self.serverChan = serverChan or {}
        if not self.serverChan:
            print(u'没有配置 serverChan 的密钥')

        # serverChan 的汇报地址
        self.serverChanFormat = u"https://sc.ftqq.com/{SCKEY}.send?text={text}&desp={desp}"

        self.mongourl = 'mongodb://{username}:{password}@{host}:{port}/{dbn}?authMechanism=SCRAM-SHA-1'.format(
            **self.mongoSetting)

        self.__active = False

        # 下次查看是否已经完成任务的时间
        self.nextWatchTime = datetime.datetime.now()

        # 关闭服务的信号
        for sig in [signal.SIGINT,  # 键盘中 Ctrl-C 组合键信号
                    signal.SIGHUP,  # nohup 守护进程发出的关闭信号
                    signal.SIGTERM,  # 命令行数据 kill pid 时的信号
                    ]:
            signal.signal(sig, self.shutdown)

        self.authed = False

        # 初始化

        self.init()

    def initLog(self, loggingconf):
        """
        初始化日志
        :param loggingconf:
        :return:
        """
        if loggingconf:
            # log4mongo 的bug导致使用非admin用户时，建立会报错。
            # 这里使用注入的方式跳过会报错的代码
            log4mongo.handlers._connection = pymongo.MongoClient(
                host=loggingconf['handlers']['mongo']['host'],
                port=loggingconf['handlers']['mongo']['port'],
            )

            logging.config.dictConfig(loggingconf)
            self.log = logging.getLogger(self.name)

        else:
            self.log = logging.getLogger()
            self.log.setLevel('DEBUG')
            fmt = "%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s"
            # datefmt = "%a-%d-%b %Y %H:%M:%S"
            datefmt = None
            formatter = logging.Formatter(fmt, datefmt)
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(formatter)
            sh.setLevel('DEBUG')
            self.log.addHandler(sh)

            sh = logging.StreamHandler(sys.stderr)
            sh.setFormatter(formatter)
            sh.setLevel('WARN')
            self.log.addHandler(sh)
            self.log.warn(u'未配置 loggingconfig')

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
            self.mongoclient = pymongo.MongoClient(
                host=self.mongoSetting['host'],
                port=self.mongoSetting['port']
            )
            if self.mongoSetting.get('username'):
                # self.mongoclient = pymongo.MongoClient(self.mongourl)
                self.authed = self.db.authenticate(
                    self.mongoSetting['username'],
                    self.mongoSetting['password']
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

        # 最后更新任务时间
        self.refreshWatchTime()

    def _run(self):
        """

        :return:
        """
        # 下次任务时间
        self.reportWatchTime()

        while self.__active:
            now = datetime.datetime.now()
            if now < self.nextWatchTime:
                time.sleep(1)
                continue

            self.log.info(u'达到截止时间')

            # 检查任务
            self.checkTask()

            # 任务排序
            self.sortTask()

            # 最后更新任务时间
            self.refreshWatchTime()

            # 下次任务时间
            self.reportWatchTime()
    def reportWatchTime(self):
        """
        下次任务的时间
        :return:
        """
        now = datetime.datetime.now()
        if now < self.nextWatchTime:
            # 还没到观察下一个任务的时间
            rest = self.nextWatchTime - now
            self.log.info(u'下次截止时间 {}'.format(self.nextWatchTime))
            # time.sleep(rest.total_seconds())
            # self.log.info(u'达到截止时间')

    def start(self):
        """

        :return:
        """
        self.__active = True
        try:
            self._run()
        except Exception as e:
            print(e.message)
            self.log.critical(e.message)
            self.stop()

    def stop(self):
        """
        关闭服务
        :return:
        """
        self.__active = False
        self.log.info(u'服务即将关闭……')

    def shutdown(self, signalnum, frame):
        """
        处理 signal 信号触发的结束服务信号
        :param signalnum:
        :param frame:
        :return:
        """
        self.stop()

    def __del__(self):
        """
        实例释放时的处理
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        try:
            if self.authed:
                self.db.logout()
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
            if t['off']:
                continue
            t.pop('_id')
            taskList.append(Task(**t))

        self.tasks = taskList
        self.log.info(u'加载了 {} 个任务'.format(len(self.tasks)))
        if __debug__:
            for t in self.tasks:
                self.log.debug(str(t))


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
            assert isinstance(t, Task)
            if now >= t.deadline:
                taskList.append(t)
                try:
                    # 最早开始的一个任务
                    if firstLanuchTime < t.lanuchTime:
                        firstLanuchTime = t.lanuchTime
                except TypeError:
                    firstLanuchTime = t.lanuchTime

        self.log.info(u'查询启动报告时间 > {}'.format(firstLanuchTime))

        # 查询 >firstLanuchTime 的启动报告
        sql = {
            'datetime': {
                '$gte': firstLanuchTime,
            }
        }

        reportCol = self.db[self.reportCollectionName]
        cursor = reportCol.find(sql)

        if __debug__:
            self.log.debug(u'查询到 {} 条报告'.format(cursor.count()))

        # 核对启动报告
        for report in cursor:
            for t in taskList:
                assert isinstance(t, Task)
                if t.isReport(report):
                    # 完成了，刷新deadline
                    self.log.info(u'{} 服务启动完成 {}'.format(t.name, t.lanuchTime))
                    if t.isLate:
                        # 迟到的启动报告, 也需要发通知
                        self.noticeDealyReport(t)
                    t.finishAndRefresh()
                    taskList.remove(t)
                    break

        # 未能准时启动的服务
        for t in taskList:
            self.noticeUnreport(t)
            # 设置为启动迟到
            t.setLate()
            # 未完成，将 deadline 延迟到1分钟后
            t.delayDeadline()

    def noticeDealyReport(self, task):
        """

        :param task: tasks.Task
        :param report: dict()
        :return:
        """
        # 通知：任务延迟完成了
        text = u'服务{name}启动迟到'.format(name=task.name)
        desp = u'当前时间:{}'.format(datetime.datetime.now())

        for k, v in task.toNotice().items():
            desp += u'\n\n{}\t:{}'.format(k, v)

        self.sendServerChan(text, desp)

    def noticeUnreport(self, task):
        """
        :param task: tasks.Task
        :return:
        """
        # 通知：未收到任务完成通知
        text = u'服务{name}未启动'.format(name=task.name)
        desp = u'当前时间\t:{}'.format(datetime.datetime.now())

        for k, v in task.toNotice().items():
            desp += u'\n\n{}\t:{}'.format(k, v)

        self.sendServerChan(text, desp)

    def sendServerChan(self, text, desp):
        """

        :return:
        """
        for account, SCKEY in self.serverChan.items():
            url = self.serverChanFormat.format(SCKEY=SCKEY, text=text, desp=desp)
            while True:
                r = requests.get(url)
                if r.status_code == 200:
                    # 发送异常，重新发送
                    break
                self.log.warn(u'向serverChan发送信息异常 code:{}'.format(r.status_code))
                time.sleep(10)

            self.log.info(u'向 {} 发送信息 '.format(account))

    def createTask(self, **kwargs):
        """
        创建任务
        :param kwargs:
        :return:
        """
        newTask = Task(**kwargs)

        sql = newTask.toSameTaskKV()
        dic = newTask.toMongoDB()

        self.db.task.update_one(sql, {'$set': dic}, upsert=True)
        # self.db.task.find_one_and_update(sql, {'$set': dic}, upsert=True)
        self.log.info(u'创建了task {}'.format(str(dic)))

    def showTask(self):
        """

        :return:
        """
        for t in self.tasks:
            print(t.toMongoDB())
