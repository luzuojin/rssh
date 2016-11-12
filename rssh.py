#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import base64

# sys.stdout.write("\x1b]2;Another Title\x07")
# sys.stdout.write("\033]0;Another Title\007")
# 'echo -ne "\033]0;${USER}@${HOSTNAME}\007"'


class Session:
    host = ''
    port = 0
    user = ''
    pawd = ''
    alias= ''

    def __init__(self, host, port, user, pawd, alias):
        self.host = host
        self.port = port
        self.user = user
        self.pawd = pawd
        self.alias = alias

    def sshLogin(self):
        loginCmd = "ssh %s@%s -p%s" % (self.user, self.host, self.port)
        child = pexpect.spawn(loginCmd)
        index = child.expect(['password:','\(yes/no\)\?', pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            child.sendline(self.pawd)
            child.interact()
        elif index == 1:
            child.sendline('yes')
            child.expect(['password:'])
            child.sendline(self.pawd)
            child.interact()
        elif index == 2:
            print "子程序异常，退出!"
            child.close()
        elif index == 3:
            print "连接超时"

    def toTxt(self):
        return self.alias + '\t' + self.host + '\t' + self.port + '\t' + self.user + '\t' + base64.b64encode(self.pawd)

    def toStr(self):
        return self.alias + '\t' + self.user + '\t' + self.host + '\t' + self.port + '\t' + self.pawd

def parse(txt):
    txt = txt.strip('\n')
    arr = txt.split('\t')
    return Session(arr[1], arr[2], arr[3], base64.b64decode(arr[4]), arr[0])

def loadConf(conf=os.path.expanduser('~/.rssh')):
    file = open(conf, 'r')
    lines = file.readlines()
    sessions = {}
    for line in lines:
        session = parse(line)
        sessions[session.alias] = session
    file.close()
    return sessions

def writeConf(sessions, conf=os.path.expanduser('~/.rssh')):
    file = open(conf, 'w')
    for key in sessions:
        session = sessions[key]
        file.write(session.toTxt())
        file.write('\n')
    file.close()

def add(alias, shost, port='22'):
    user = 'root'
    host = shost
    if '@' in shost:
        user = shost[:shost.index('@')]
        host = shost[shost.index('@')+1:]
    pawd = raw_input("Password:")
    sessions = loadConf()
    sessions[alias] = Session(host, port, user, pawd, alias)
    writeConf(sessions)

def remove(alias):
    sessions = loadConf()
    del sessions[alias]
    writeConf(sessions)

def list():
    print
    sessions = loadConf()
    for key in sessions:
        session = sessions[key]
        print session.alias + '\t' + session.host

def edit(alias):
    sessions = loadConf()
    if alias not in sessions:
        print alias + ' not exists'
    else :
        session = sessions[alias]
        pawd = raw_input("Password:")
        session.pawd = pawd
        writeConf(sessions)

def login(alias):
    sessions = loadConf()
    if alias not in sessions:
        print alias + ' not exists'
    else:
        session = sessions[alias]
        # setTitle(session)
        # session.sshLogin()
        print session.toStr()


def setTitle(session):
    os.environ["TERM"] = "vt100"
    sys.stdout.write("\033]0;%s ~ %s@%s\007" % (session.alias, session.user, session.host))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'rssh {alias|ls|rm|add}'
        exit(0)

    if 'ls' == sys.argv[1]:
        list()
    elif 'rm' == sys.argv[1]:
        remove(sys.argv[2])
    elif 'add' == sys.argv[1]:
        add(sys.argv[2], sys.argv[3])
    elif 'edit' == sys.argv[1]:
        edit(sys.argv[2])
    else:
        login(sys.argv[1])


