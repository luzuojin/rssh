### Install
```bash
#dependence
pip install paramiko
pip install pexpect

#set path
rssh install
```
### Usage
```bash
#session
rssh add alias user(root)@host port(22)
rssh edit alias
rssh rm alias
#list
rssh ls

#ssh login
rssh alias

#rsync
rssh put alias dest source
rssh get alias source dest

#remote sh exec
rssh exec alias cmd
#remote curl(127.0.0.1)
rssh call alias port uri
```
