# coding:utf-8

"""
测试在各个节点发送邮件的单元测试
"""
import arrow
import pytest
import logging


def test_eamil_list(monitor):
    """
    邮件通知列表不能为空
    :param monitor:
    :return:
    """
    assert monitor.email.to_addr


def test_send_email(monitor):
    """
    将 warning 以上的日志发送邮件
    :return:
    """

    subject, text = '单元测试邮件', '单元测试内容'
    monitor.email.send(subject, text)


def test_send_serverChan(monitor):
    import datetime
    subject, text = '单元测试微信', '单元测试微信内容 {}'.format(datetime.datetime.now())
    monitor.email._sendToServerChan(subject, text)


def test_send_log_warning(monitor):
    monitor.log.warning('单元测试中 waring 日志')
    monitor.log.error('单元测试中 error 日志')
    monitor.log.critical('单元测试中 critical 日志')
    monitor._logWarning()


def test_notice_heart_beat(monitor):
    noHeartBeats = [
        {'host': '192.168.31.208', 'type': 'svnpy_turtle', 'name': 'simSvnpyTurtle',
         'datetime': arrow.now().datetime
         }
    ]
    monitor.noticeHeartBeat(noHeartBeats)