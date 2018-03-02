# coding:utf-8
import traceback
import requests
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from threading import Thread

import smtplib


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


class EMail(object):
    """

    """

    def __init__(self, from_name, from_addr, password, to_addr, smtp_server, smtp_port, serverChan):
        self.from_name = from_name
        self.from_addr = from_addr  # 发送者
        self.password = password
        self.to_addr = to_addr
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sendingmail = None

        self.serverChan = serverChan or {}  # {'adm': 'serverChanUrl'}
        if self.serverChan:
            for account, url in self.serverChan.items():
                serverChanUrl = requests.get(url).text
                self.serverChan[account] = serverChanUrl

    def send(self, subject, text):
        self.sendingmail = Thread(target=self._send, args=(subject, text), daemon=True)
        self.sendingmail.start()

    def _send(self, subject, text):
        try:
            text = text.replace('\r\n', '\n').replace('\n', '\r\n')
            msg = MIMEText(text, 'plain', 'utf-8')
            msg['From'] = _format_addr('%s <%s>' % (self.from_name, self.from_addr))
            msg['To'] = _format_addr('程序通知 <%s>' % self.to_addr)
            msg['Subject'] = Header(subject, 'utf-8').encode()

            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            # server.set_debuglevel(0)
            server.login(self.from_addr, self.password)
            server.sendmail(self.from_addr, [self.to_addr], msg.as_string())
            server.quit()
        except Exception:
            # 发送失败，使用微信汇报
            if self.serverChan:
                self._sendToServerChan('%s 发送邮箱失败' % self.from_name, traceback.format_exc())
                time.sleep(10)
                self._sendToServerChan('{}发送失败内容'.format(self.from_name), 'title: {}\n{}'.format(subject, text))

    def _sendToServerChan(self, text, desp):
        desp = desp.replace('\n\n', '\n').replace('\n', '\n\n')
        for account, serverChanUrl in self.serverChan.items():
            url = serverChanUrl.format(text=text, desp=desp)
            count = 0
            while count < 5:
                count += 1
                r = requests.get(url)
                if r.status_code != 200:
                    # 发送异常，重新发送
                    time.sleep(10)
                    continue
                else:
                    # 发送成功
                    break

    def __del__(self):
        if self.sendingmail and self.sendingmail.is_alive():
            self.sendingmail.join(11)
