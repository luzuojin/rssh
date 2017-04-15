#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import base64
import pexpect
import paramiko
from collections import OrderedDict

class Session:
    def __init__(self, host, port, user, pawd, alias):
        self.host = host
        self.port = port
        self.user = user
        self.pawd = pawd
        self.alias = alias

    def sshLogin(self):
        loginCmd = "ssh %s@%s -p%s -o TCPKeepAlive=yes -o ServerAliveInterval=30" % (self.user, self.host, self.port)
        print loginCmd
        self.expectExec(loginCmd)

    def expectExec(self, cmd):
        child = pexpect.spawn(cmd)
        index = child.expect(['assword:','\(yes/no\)\?', pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            child.sendline(self.pawd)
            interact(child)
        elif index == 1:
            child.sendline('yes')
            child.expect(['assword:'])
            child.sendline(self.pawd)
            interact(child)
        elif index == 2:
            print child.before
            child.close()
        elif index == 3:
            print "connect timeout"
            print child.before
            child.close()

    def remoteExec(self, cmd):
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, int(self.port), self.user, self.pawd, timeout=5)

            chan = ssh.get_transport().open_session()
            chan.get_pty()
            chan.exec_command(cmd)
            ret = ''
            while True:
                if chan.recv_ready() or chan.recv_stderr_ready:
                    r = chan.recv(1024)
                    ret += r
                if chan.exit_status_ready():
                    break
            return ret
        finally :
            if ssh:
                ssh.close()


    def toTxt(self):
        return self.alias + '\t' + self.host + '\t' + self.port + '\t' + self.user + '\t' + base64.b64encode(self.pawd)

    def toStr(self):
        return self.alias + '\t' + self.user + '\t' + self.host + '\t' + self.port + '\t' + self.pawd

def interact(child):
    winsz = getWinsz()
    child.setwinsize(winsz[0], winsz[1])
    child.interact()

def getWinsz():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            pass
    return ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)

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

def getSession(alias):
    sessions = loadConf()
    if alias not in sessions:
        print alias + ' not exists'
    else:
        return sessions[alias]

def add(alias, shost, port='22'):
    user = 'root'
    host = shost
    if '@' in shost:
        user = shost[:shost.index('@')]
        host = shost[shost.index('@')+1:]
    pawd = raw_input("Password: ")
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
    for key in sorted(sessions):
        session = sessions[key]
        print session.alias + '\t' + session.host

def show(alias):
    session = getSession(alias)
    if session:
        print session.toStr()

def move(alias, new_alias):
    sessions = loadConf()
    if alias not in sessions:
        print alias + ' not exists'
    else:
        session = sessions[alias]
        session.alias = new_alias
        writeConf(sessions)

def edit(alias):
    sessions = loadConf()
    if alias not in sessions:
        print alias + ' not exists'
    else :
        session = sessions[alias]
        host = raw_input("Host: ")
        if host:
            if '@' in host:
                session.user = host[:host.index('@')]
                session.host = host[host.index('@')+1:]
            else:
                session.host = host
        port = raw_input("Port: ")
        if port:
            session.port = port
        pawd = raw_input("Password: ")
        if pawd:
            session.pawd = pawd
        writeConf(sessions)

def rsync(session, source, dest):
    cmd = "rsync -progress -avztr --timeout=600 -e'ssh -p %s' %s %s" % (session.port, source, dest)
    print cmd
    session.expectExec(cmd)

def get(alias, source, dest):
    session = getSession(alias)
    rsource = '%s@%s:%s' % (session.user, session.host, source)
    rsync(session, rsource, dest)

def put(alias, dest, source):
    session = getSession(alias)
    rdest = '%s@%s:%s' % (session.user, session.host, dest)
    rsync(session, source, rdest)

def exec0(alias, cmd):
    session = getSession(alias)
    print cmd
    print session.remoteExec(cmd)

def login(alias):
    session = getSession(alias)
    if session:
        setTitle(session)
        session.sshLogin()

def setTitle(session):
    os.environ["TERM"] = "vt100"
    sys.stdout.write("\033]0;%s ~ %s@%s\007" % (session.alias, session.user, session.host))


class Option:
    def __init__(self, func, args, hint):
        self.func= func
        self.args= args
        self.hint= hint

    def execute(self,args):
        self.func(*args)

options = OrderedDict([
    ('ls'  , Option(list, 0, '')),
    ('add' , Option(add, 2, 'alias user(root)@host port(22)')),
    ('edit', Option(edit, 1, 'alias')),
    ('rm'  , Option(remove, 1, 'alias')),
    ('mv'  , Option(move, 2, 'alias new_alias')),
    ('put' , Option(put, 3, 'alias dest source')),
    ('get' , Option(get, 3, 'alias source dest')),
    ('exec', Option(exec0, 2, 'alias cmd')),
    ('show', Option(show, 1, 'alias')),
    ('login',Option(login, 1, 'alias'))
])

def doOption(key, args):
    if key in options:
        option = options[key]
        if len(args) < option.args:
            print 'rssh %s %s' % (key, option.hint)
        else:
            option.execute(args)
    else:
        login(key)

if __name__ == '__main__':
    args = sys.argv
    if len(args) == 1:
        print 'rssh {%s}' % ('|'.join(options.keys()))
    elif 'test' == args[1]:
        print "OK" if len(args) == 2 or args[2] in options else "None"
    else:
        doOption(args[1], args[2:])
