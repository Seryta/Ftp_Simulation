#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author Saryta
# @last-modified 2020-12-03T21:52:28.886Z+08:00

import socket
import os
import getpass
import json
import struct
# import time
# import hashlib
# import threading


class Ftp_Client(object):
    def __init__(self, ip, port):
        self.client = socket.socket()
        self.ip = ip
        self.port = port
        self.__connect()
        print("连接成功。。。")
        self.__interactive()

    def __connect(self):
        self.client.connect((self.ip, self.port))
        self.client.settimeout(5)
        print("等待连接。。。")

    def __interactive(self):
        flag = '0'
        while flag != 'q':
            flag_in = input("请选择：\n1. 登录用户 \n2. 退出\n>: ")
            if flag_in.isdigit():
                flag_in = int(flag_in)
                if flag_in == 2:
                    flag = 'q'
                    self.__send(str(flag))
                    self.client.close()
                    print('Bye~')
                    break
                elif flag_in == 1:
                    self.__send(str(flag_in))
                else:
                    flag = '0'
                    continue
            else:
                flag = '0'
                continue

            status = self.__login()
            while status != 'exit':
                cmd = input(">: ").split()
                if len(cmd) > 0:
                    if hasattr(Ftp_Client, 'client_' + cmd[0]):
                        self.__send(json.dumps(cmd))
                        if self.__response():
                            status = getattr(Ftp_Client,
                                             'client_' + cmd[0])(self, cmd)
                        else:
                            continue
                    elif cmd[0] == 'exit':
                        status = cmd[0]
                        self.__send(json.dumps(['exit']))
                    else:
                        self.client_help(cmd)
                        self.__send(json.dumps(['exit']))
        return

    def __send(self, data):
        msg_bs = data.encode('utf-8')
        msg_struct_len = struct.pack('i', len(msg_bs))
        self.client.send(msg_struct_len)
        self.client.send(msg_bs)
        return

    def __recv(self):
        msg_struct_len = self.client.recv(4)
        msg_len = struct.unpack('i', msg_struct_len)[0]
        msg_bs = self.client.recv(msg_len)
        return msg_bs

    def __login(self):
        username = input('Username: ')
        passwd = getpass.getpass('Password: ')
        self.__send(username)
        self.__send(passwd)
        verify = self.__response()
        if verify:
            print(("欢迎{}登录FTP！").format(username))
            return
        else:
            return 'exit'

    def client_put(self, cmd):
        if len(cmd) < 2:
            return
        for file_path in cmd[1:]:
            if os.path.isfile(file_path):
                file_size = os.stat(file_path).st_size
                send_size = 0
                self.__send(str(file_size))
                if not self.__response():
                    continue
                f = open(file_path, 'r')
                for line in f:
                    print('\r' + '-' * int(send_size / file_size * 50) + '>  ',
                          str(int(send_size / file_size * 100)) + '%',
                          end='')
                    self.__send(line)
                    send_size += len(line)
                    if send_size == file_size:
                        print('\r' + '-' * 50 + '>  ', +str(100) + '%')
                        print("\n传输结束！")
                f.close()
            else:
                self.__send('continue')
                self.__response()
                continue
            # md5_result = {}
            # for file_name in cmd[1:]:
            #     md5_result[file_name] = threading.Thread(target=self.__md5sum,
            #                                              args=(file_name))
            #     print(file_name, md5_result[file_name], sep='：')
        return

    def client_get(self, cmd):
        if len(cmd) < 2:
            print('get filename...')
            return
        for file_name in cmd[1:]:
            if not self.__response():
                continue
            file_size = 0
            recv_size = 0
            if os.path.isfile(file_name):
                f = open(file_name + '.new', 'wb')
            else:
                f = open(file_name, 'wb')
            file_size = int(self.__recv().decode('utf-8'))
            while not recv_size > file_size:
                print('\r' + '-' * int(recv_size / file_size * 50) + '>  ',
                      str(int(recv_size / file_size * 100)) + '%',
                      end='')
                if recv_size == file_size:
                    break
                data = self.__recv()
                f.write(data)
                recv_size += len(data)
            f.close()
            print("\n传输结束！")
            # md5_result = {}
            # for file_name in cmd[1:]:
            #     md5_result[file_name] = threading.Thread(target=self.__md5sum,
            #                                              args=(file_name))
            #     print(file_name, md5_result[file_name], sep='：')
            return

    def client_pwd(self, cmd):
        pwd_data = self.__recv().decode('utf-8')
        print(pwd_data)
        return

    def client_ls(self, cmd):
        if len(cmd) > 1:
            for i in cmd[1:]:
                ls_data = self.__recv()
                print(ls_data.decode('utf-8'))
        else:
            ls_data = self.__recv()
            print(ls_data.decode('utf-8'))
        return

    def client_cd(self, cmd):
        self.__response()
        return

    def client_help(self, cmd):
        cmd_list = {
            'ls':
            'List information about the FILEs (the current directory by default).',
            'cd': 'Cd changes the current working directory.',
            'pwd': 'Output the current working directory.',
            'put': 'Upload file.',
            'get': 'Download file.',
            'exit': 'Exit'
        }
        _, paras = cmd[0], cmd[1:]
        if len(paras) > 0:
            for para in paras:
                if para in cmd_list:
                    print("{}   -   {}".format(para, cmd_list[para]))
        else:
            for key, value in cmd_list.items():
                print("{}   -   {}".format(key, value))
        return

    # def __md5sum(self, filename):
    #     md5 = hashlib.md5()
    #     with open(filename, 'rb') as f:
    #         for line in f:
    #             md5.update(line)
    #     return md5.hexdigest()

    def __response(self):
        server_res = self.__recv().decode('utf-8')
        resps = {
            '000': True,
            '001': 'Forbidden!',
            '002': 'File does not exist!',
            '003': 'Directory does not exist!',
            '004': 'Command not found!',
            '005': 'User does not exist!',
            '006': 'Wrong Password!',
            '007': 'Command False!',
            '008': 'File is too large! Forbidden!'
        }
        if server_res == '000':
            return resps[server_res]
        else:
            print(resps[server_res])
            return False


if __name__ == "__main__":
    ip = input("Ftp server's IP: ")
    port = int(input("Ftp server's PORT: "))
    Ftp_Client(ip, port)
