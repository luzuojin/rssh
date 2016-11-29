#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import base64
import pexpect
import paramiko

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
        self.execute(loginCmd)

    def execute(self, cmd):
        child = pexpect.spawn(cmd)
        index = child.expect(['assword:','\(yes/no\)\?', pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            child.sendline(self.pawd)
            child.interact()
        elif index == 1:
            child.sendline('yes')
            child.expect(['assword:'])
            child.sendline(self.pawd)
            child.interact()
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
    for key in sessions:
        session = sessions[key]
        print session.alias + '\t' + session.host

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
    session.execute(cmd)

def get(alias, source, dest):
    session = getSession(alias)
    rsource = '%s@%s:%s' % (session.user, session.host, source)
    rsync(session, rsource, dest)

def put(alias, dest, source):
    session = getSession(alias)
    rdest = '%s@%s:%s' % (session.user, session.host, dest)
    rsync(session, source, rdest)

def call(alias, port, uri):
    cmd = 'curl "http://127.0.0.1:%s/%s"' % (port, uri)
    exec0(alias, cmd)

def exec0(alias, cmd):
    session = getSession(alias)
    print cmd
    print session.remoteExec(cmd)

def login(alias):
    session = getSession(alias)
    if session:
        # setTitle(session)
        # session.sshLogin()
        print session.toStr()

def setTitle(session):
    os.environ["TERM"] = "vt100"
    sys.stdout.write("\033]0;%s ~ %s@%s\007" % (session.alias, session.user, session.host))

if __name__ == '__main__':
    args = sys.argv
    argsnum = len(args)
    if argsnum == 1:
        print 'rssh {alias|ls|rm|add|get|put}'
        exit(0)

    if 'ls' == args[1]:
        list()
    elif 'rm' == args[1]:
        if argsnum < 3:
            print 'rssh rm alias'
        else:
            remove(args[2])
    elif 'add' == args[1]:
        if argsnum < 4:
            print 'rssh add alias user@host port (optional [user@|port])'
        elif argsnum == 4:
            add(args[2], args[3])
        else:
            add(args[2], args[3], args[4])
    elif 'edit' == args[1]:
        if argsnum < 3:
            print 'rssh edit alias'
        else:
            edit(args[2])
    elif 'get' == args[1]:
        if argsnum < 5:
            print 'rssh get alias source dest'
        else:
            get(args[2], args[3], args[4])
    elif 'put' == args[1]:
        if argsnum < 5:
            print 'rssh put alias dest source'
        else:
            put(args[2], args[3], args[4])
    elif 'call' == args[1]:
        if argsnum < 5:
            print 'rssh call alias port uri'
        else:
            call(args[2], args[3], args[4])
    elif 'exec' == args[1]:
        if argsnum < 4:
            print 'rssh exec alias cmd'
        else:
            exec0(args[2], args[3])
    else:
        login(args[1])


