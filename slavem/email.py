# coding:utf-8
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

    def __init__(self, from_name, from_addr, password, to_addr, smtp_server, smtp_port):
        self.from_name = from_name
        self.from_addr = from_addr  # 发送者
        self.password = password
        self.to_addr = to_addr
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sendingmail = None

    def send(self, subject, text):
        self.sendingmail = Thread(target=self._send, args=(subject, text), daemon=True)
        self.sendingmail.start()

    def _send(self, subject, text):
        msg = MIMEText(text, 'plain', 'utf-8')
        msg['From'] = _format_addr('%s <%s>' % (self.from_name, self.from_addr))
        msg['To'] = _format_addr('程序通知 <%s>' % self.to_addr)
        msg['Subject'] = Header(subject, 'utf-8').encode()

        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.set_debuglevel(1)
        server.login(self.from_addr, self.password)
        server.sendmail(self.from_addr, [self.to_addr], msg.as_string())
        server.quit()

    def __del__(self):
        if self.sendingmail and self.sendingmail.is_alive():
            self.sendingmail.join(3)