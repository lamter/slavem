# coding:utf-8
import traceback
import requests
import time
import logging
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
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sendingmail = None

        self.to_addr = to_addr.copy() or {}  # # {'adm': 'email_addr'}
        if self.to_addr:
            for account, url in self.to_addr.items():
                emailAddr = requests.get(url).text.strip('\n')
                self.to_addr[account] = emailAddr

        self.serverChan = serverChan or {}  # {'adm': 'serverChanUrl'}
        if self.serverChan:
            for account, url in self.serverChan.items():
                serverChanUrl = requests.get(url).text
                if not serverChanUrl.startswith('https://sc.ftqq.com/'):
                    raise ValueError('加载serverChan地址异常 {}'.format(serverChanUrl))

                self.serverChan[account] = serverChanUrl

    def send(self, subject, text):
        self.sendingmail = Thread(target=self._send, args=(subject, text))
        self.sendingmail.start()

    def _send(self, subject, _text):
        try:
            text = _text.replace('\r\n', '\n').replace('\n', '\r\n')
            msg = MIMEText(text, 'plain', 'utf-8')
            msg['From'] = _format_addr('%s <%s>' % (self.from_name, self.from_addr))
            msg['To'] = _format_addr('程序通知 <%s>' % self.to_addr)
            msg['Subject'] = Header(subject, 'utf-8').encode()

            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            # server.set_debuglevel(0)
            server.login(self.from_addr, self.password)
            server.sendmail(self.from_addr, list(self.to_addr.values()), msg.as_string())
            server.quit()
        except Exception:
            # 发送失败，使用微信汇报
            self._sendFail2ServerChan(subject, _text)

    def _sendFail2ServerChan(self, subject, text):
        logging.warning('发送邮件失败 \n {}\n{}'.format(subject, text))
        if self.serverChan:
            self._sendToServerChan('%s 发送邮箱失败' % self.from_name, traceback.format_exc())
            time.sleep(10)
            self._sendToServerChan('{}发送失败内容'.format(self.from_name), 'title: {}\n{}'.format(subject, text))

    def _sendToServerChan(self, text, desp):
        desp = desp.replace('\n\n', '\n').replace('\n', '\n\n')
        for account, serverChanUrl in self.serverChan.items():
            try:
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
                        time.sleep(1)
                        break
            except Exception:
                print(serverChanUrl)
                traceback.print_exc()
