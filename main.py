#!/usr/bin/env python3
# coding=utf-8

import os
import configparser
import subprocess
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


class Project(object):

    def __init__(self, name, path, exucmd, maintainer=None, cclist=None,
                 period=None, sendFile=None):
        self._name = name
        self._path = path
        self._exucmd = exucmd
        self._maintainer = maintainer
        self._cclist = cclist
        self._period = period
        self._sendFile = sendFile
        self._outputLog = ""

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def exucmd(self):
        return self._exucmd

    @exucmd.setter
    def exucmd(self, value):
        self._exucmd = value

    @property
    def maintainer(self):
        return self._maintainer

    @maintainer.setter
    def maintainer(self, value):
        self._maintainer = value

    @property
    def cclist(self):
        return self._cclist

    @cclist.setter
    def cclist(self, value):
        self._cclist = value

    @property
    def period(self):
        return self._period

    @period.setter
    def period(self, value):
        self._period = value

    @property
    def sendFile(self):
        return self._sendFile

    @sendFile.setter
    def sendFile(self, value):
        self._sendFile = value

    @property
    def outputLog(self):
        return self._outputLog

    @outputLog.setter
    def outputLog(self, value):
        self._outputLog = value


class AutoScript(object):

    def __init__(self):

        # mailing property

        self.mailingPropertyPath = "/home/isobuilder/.cache/jenkins/workspace/AutoScriptProperty/property.ini"
        #self.mailingPropertyPath = "./property.ini"
        (self.smtpserver, self.username, self.password,
         self.sender) = self.getMailingProperty()

        # mailing
        self.smtp = smtplib.SMTP()
        self.smtp.connect(self.smtpserver)
        self.smtp.login(self.username, self.password)
        print("SMTP Service is ready!")

        self.propertyFileName = "AUTO.ini"
        self.allProjects = self.getAllProjects()

        self.projectOutputFile = "__OUTPUT__.log" 

        # start
        self.work(self.allProjects)


    def getMailingProperty(self):
        config = configparser.ConfigParser()
        config.read(self.mailingPropertyPath)
        return config["DEFAULT"]["SMTPServer"], config["DEFAULT"]["UserName"], \
            config["DEFAULT"]["Password"], config["DEFAULT"]["Sender"]

    def getAllProjects(self):
        allProjects = []
        allDirs = list(map(lambda f: os.path.join(os.getcwd(), f),
                           list(filter(lambda f: os.path.isdir(f),
                                       os.listdir("./")))))
        proDirs = list(filter(lambda d: self.propertyFileName in
                              os.listdir(d), allDirs))
        for proDir in proDirs:
            config = configparser.ConfigParser()
            config.read(os.path.join(proDir, self.propertyFileName))
            if config["SYSTEM"]["Enable"] != "1":
                continue
            project = Project(config["DEFAULT"]["Name"], proDir,
                              config["DEFAULT"]["EXUCMD"],
                              config["DEFAULT"]["Maintainer"],
                              config["DEFAULT"]["CCList"],
                              config["DEFAULT"]["Period"],
                              config["DEFAULT"]["SendFile"]
                              )
            allProjects.append(project)

        return allProjects

    def work(self, allProjects):
        failProjects = []
        for project in allProjects:
            print("cmd:", project.exucmd)
            os.chdir(project.path)
            try:
                subprocess.check_output(project.exucmd.split(" "))
                print("Script: %s, excuted successfully!" % (project.name))
            except subprocess.CalledProcessError as e:
                print("Script: %s, excuted fail!" % (project.name))
                print("Script output: %s" % e.output)
                with open(self.projectOutputFile, "w") as f:
                    f.write(str(e.output))
                failProjects.append(project)

        # send mails
        if len(failProjects) > 0:
            for project in failProjects:
                print("Protject(%s) is sending mail" % project.name)
                self.sendMail(project)

    def sendMail(self, project):
        # collect the attach
        msgRoot = MIMEMultipart("related")
        msgRoot["Subject"] = "Deepin-CI/AutoScript: %s" % project.name
        sendFiles = list(filter(lambda f: len(f) > 0, \
                                project.sendFile.split(" ")))
        sendFiles.append(self.projectOutputFile)
        print(sendFiles)
        for sendFile in sendFiles:
            att = MIMEText(open(os.path.join(project.path, sendFile),
                                "r").read(), "base64", "utf-8")
            att["Content-Type"] = "application/octet-stream"
            att["Content-Disposition"] = 'attachment; filename="%s"'\
                % sendFile
            msgRoot.attach(att)

        cclist = list(filter(lambda address: len(address) > 0,
                             project.cclist.split(";")))
        self.smtp.sendmail(self.sender, cclist, msgRoot.as_string())
        print("Mail: successfully")

if __name__ == "__main__":
    autoscript = AutoScript()
