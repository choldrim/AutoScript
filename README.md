#AutoScript
##Descript
####A series of scripts which are run in deepin jenkins.

##Extends
#####Just add a folder(such as: ExampleScript) in the main directory, and then add a AUTO.ini configuration file in this folder. As long as consistent with the preparation of the rules of AUTO.ini, it will become a automatic and runnable project in Jenkins.

##AUTO.ini
```ini
[DEFAULT]
Name = Hello Script  
Maintainer = tangcaijun@foxmail.com  
CCList = 2013360448@qq.com,tangcaijun@linuxdeepin.com
SendFile = output.log hello.txt  
Period = H H(0-6) * * *  
EXUCMD = python3 check.py  
  
[SYSTEM]  
Enable = 0  ;this project will be closed by set "Enable = 0"  
```
