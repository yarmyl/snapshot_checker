#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paramiko


class sshConnect:

    def __init__(self, conn):
        host = conn['host']
        user = conn['user']
        passwd = conn.get('pass')
        port = int(conn['port']) if conn.get('port') else 22
        self.percent = int(conn['percent']) if conn.get('percent') else 50
        self.count = int(conn['count']) if conn.get('count') else 2
        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.__client.connect(
                hostname=host, username=user, password=passwd, port=port)
        except Exception:
            print("Failed to connect!")

    def __del__(self):
        self.__client.close()

    def get_cmd(self, command):
        stdin, stdout, stderr = self.__client.exec_command(command)
        data = stdout.read().decode()  # + stderr.read().decode()
        return data
