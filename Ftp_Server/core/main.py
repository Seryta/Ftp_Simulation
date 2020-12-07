#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @author Saryta
# @last-modified 2020-12-03T22:00:08.818Z+08:00

import socketserver
import os
import json
import struct
import subprocess


class Ftp_Server(socketserver.BaseRequestHandler):
    """
            '000': True,
            '001': 'Forbidden!',
            '002': 'File does not exist!',
            '003': 'Directory does not exist!',
            '004': 'Command not found!',
            '005': 'User does not exist!',
            '006': 'Wrong Password!',
            '007': 'Command False!',
            '008': 'File is too large! Forbidden!'
    """
    def handle(self):
        self.root_dir = ('/root/FTP/')
        self.home_dir = ''
        self.ch_dir = ''
        flag = '0'
        while flag != 'q':
            flag = self.__recv().decode('utf-8')
            if flag == 'q':
                continue
            if not self.__login():
                continue
            status = ''
            while status != 'exit':
                cmd = json.loads(self.__recv().decode('utf-8'))
                if hasattr(Ftp_Server, 'server_' + cmd[0]):
                    self.__send('000')
                    getattr(Ftp_Server, 'server_' + cmd[0])(self, cmd)
                elif cmd[0] == 'exit':
                    status = cmd[0]
                else:
                    self.__send('004')
        return

    def __send(self, data):
        msg_bs = data.encode('utf-8')
        msg_struct_len = struct.pack('i', len(msg_bs))
        self.request.send(msg_struct_len)
        self.request.send(msg_bs)
        return

    def __recv(self):
        msg_struct_len = self.request.recv(4)
        msg_len = struct.unpack('i', msg_struct_len)[0]
        msg_bs = self.request.recv(msg_len)
        return msg_bs

    def __login(self):
        users = os.listdir('FTP/Ftp_Server/docs/users/')
        username = self.__recv().decode('utf-8')
        passwd = self.__recv().decode('utf-8')
        if username in users:
            self.home_dir = username + '/'
            with open('FTP/Ftp_Server/docs/users/' + username) as f:
                user_info = json.loads(f.readline())
            if user_info['password'] == passwd:
                self.__send('000')
                return True
            else:
                self.__send('006')
                return False
        else:
            self.__send('005')
            return False

    def server_put(self, cmd):
        if len(cmd) < 2:
            return
        for file_name in cmd[1:]:
            file_name = file_name.split('/')[-1:][0]
            file_size = self.__recv().decode('utf-8')
            if file_size.isdigit():
                file_size = int(file_size)
            with open('FTP/Ftp_Server/docs/users/' + self.home_dir[:-1], 'r') as f:
                limit_file_size = int(json.loads(f.readline())['limit_file_size'])
            if file_size == 'continue':
                self.__send('002')
                continue
            elif file_size > limit_file_size:
                self.__send('008')
                continue
            else:
                self.__send('000')
                recv_size = 0
                print(file_name, type(file_name))
                if os.path.isfile(self.root_dir + self.home_dir + self.ch_dir +
                                  file_name):
                    f = open(
                        self.root_dir + self.home_dir + self.ch_dir +
                        file_name + '.new', 'wb')
                else:
                    f = open(
                        self.root_dir + self.home_dir + self.ch_dir +
                        file_name, 'wb')
                while recv_size < file_size:
                    data = self.__recv()
                    f.write(data)
                    recv_size += len(data)
                f.close()

    def server_get(self, cmd):
        if len(cmd) < 2:
            return
        for file_name in cmd[1:]:
            if os.path.isfile(self.root_dir + self.home_dir + self.ch_dir +
                              file_name):
                self.__send('000')
            else:
                self.__send('002')
                continue
            file_size = os.stat(self.root_dir + self.home_dir + self.ch_dir +
                                file_name).st_size
            self.__send(str(file_size))
            f = open(self.root_dir + self.home_dir + self.ch_dir + file_name,
                     'r')
            for line in f:
                self.__send(line)
            f.close()

    def server_pwd(self, cmd):
        if self.ch_dir == '':
            self.__send('/' + self.home_dir[:-1])
        else:
            self.__send('/' + self.home_dir + self.ch_dir[:-1])
        return

    def server_cd(self, cmd):
        cd_dict = {
            '.': lambda x: x,
            './': lambda x: x,
            '..': lambda x: '/'.join(x.split('/')[:-2]) + '/',
            '../': lambda x: '/'.join(x.split('/')[:-2]) + '/',
            '/': lambda x: '',
            '~/': lambda x: ''
        }
        if len(cmd) == 1:
            self.ch_dir = ''
            self.__send('000')
        elif len(cmd) == 2:
            if cmd[1] in cd_dict:
                self.ch_dir = cd_dict[cmd[1]](self.ch_dir)
                if self.ch_dir == '/':
                    self.ch_dir = ''
                self.__send('000')
            elif os.path.isdir(self.root_dir + self.home_dir + self.ch_dir +
                               cmd[1]):
                self.ch_dir += cmd[1] + '/'
                self.__send('000')
            else:
                self.__send('003')
        else:
            self.__send('007')
        return

    def server_ls(self, cmd):
        if len(cmd) > 1:
            for para in cmd[1:]:
                ls_data = self.home_dir + self.ch_dir + para
                self.__send(ls_data)
        else:
            ls_data = subprocess.getoutput(
                "ls {}".format(self.root_dir + self.home_dir + self.ch_dir))
            self.__send(ls_data)
        return


if __name__ == '__main__':
    ip = '0.0.0.0'
    port = 18899
    server = socketserver.ThreadingTCPServer((ip, port), Ftp_Server)
    server.serve_forever()
