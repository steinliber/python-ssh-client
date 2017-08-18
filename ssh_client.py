#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paramiko
import re
from paramiko.ssh_exception import AuthenticationException
import select
from termcolor import cprint
from settings import BUF_SIZE BUF_DELTA


class ClientException(Exception):
    """
    exception when connect to ssh
    """
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return 'Client Exception:%s' % msg


class SSHConnect:
    def __init__(self, host, port=22, user='develop'):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        self.host = host
        self.port = port
        self.user = user

    def __enter__(self):
        try:
            self.client.connect(self.host, self.port, self.user)
        except AuthenticationException as exc:
            raise ClientException('用户没有权限登录服务器')
        return self

    def __exit__(self, exc_type, value, trace):
        if exc_type is not None:
            raise ClientException(exc_type)
        self.client.close()

    def _tail_without_block(self, file_name):
        """
        生成每行的读取项
        """
        transport = self.client.get_transport()
        transport.set_keepalive(1)
        channel = transport.open_session()
        channel.settimeout(BUF_DELTA)
        channel.exec_command( 'killall tail')
        channel = transport.open_session()
        channel.settimeout(BUF_DELTA)
        cmd = "tail -f %s" % file_name
        channel.exec_command(cmd)
        LeftOver = ""
        while transport.is_active():
        #    print("transport is active")
            rl, wl, xl = select.select([channel], [], [], 0.0)
            if len(rl) > 0:
                buf = channel.recv(BUF_SIZE)
                if len(buf) > 0:
                    lines_to_process = LeftOver + str(
                        buf, encoding='utf8',errors='ignore')
                    EOL = lines_to_process.rfind("\n")
                    # 处理读取时不是每行末尾的问题
                    if EOL != len(lines_to_process)-1:
                        LeftOver = lines_to_process[EOL+1:]
                        lines_to_process = lines_to_process[:EOL]
                    else:
                        LeftOver = ""
                    for line in lines_to_process.splitlines():
                        yield(line)

    def tail_file(self,
                  file_name='/var/logs/collect/v3-core-develop_app/2017-08-18.log'):
        line_gen = self._tail_without_block(file_name)
        try:
            for line in line_gen:
                print(line)
        except KeyboardInterrupt:
            print('KeyboardError')


def ssh_connect(host, port=22, user='develop'):
    return SSHConnect(host, port, user)
