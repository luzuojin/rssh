### Install
```bash
#brew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew install pip

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
```
