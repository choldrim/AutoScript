#!/usr/bin/env python3
# coding=utf-8

import os
import configparser
import subprocess
import smtplib

from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Project(object):

    def __init__(self, name, path, exucmd, maintainer=None, cclist=None,
                 period=None, sendFile=None):
        self._name = name
        self._path = path
        self._exucmd = exucmd
        self._maintainer = maintainer
        self._cclist = [cc.strip() for cc in cclist.split(",") if len(cc) > 0]
        self._period = period
        self._sendFile = [f.strip() for f in sendFile.split(",") if len(f) > 0]
        self._outputLog = ""

    def __str__(self):
        return self._name

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
        if not os.path.exists(self.mailingPropertyPath):
            self.mailingPropertyPath = "./MailingProperty.ini"
        (self.smtpserver, self.username, self.password,
         self.sender) = self.getMailingProperty()
        self.subjectPrefix = "Deepin-CI/AutoScript"

        # mailing
        """
        self.smtp = smtplib.SMTP()
        if not self.readyMailingService(self.smtpserver, self.username, self.password):
            quit(1)
        print("SMTP Service is ready!")
        """

        self.propertyFileName = "AUTO.ini"
        self.scriptDir = os.path.join(os.getcwd(), "Script")
        print(self.scriptDir)
        self.allProjects = self.getAllProjects(self.scriptDir)

        self.projectOutputFile = "__SCRIPT_OUTPUT__.LOG"

        # start
        self.work(self.allProjects)

    def getMailingServiceInstance(self):
        try:
            smtp = smtplib.SMTP()
            smtp.connect(self.smtpserver)
            smtp.login(self.username, self.password)
            smtp.helo()
            return smtp
        except Exception as e:
            print("get mailing service fail")
            raise e
       

    def getMailingProperty(self):
        config = configparser.ConfigParser()
        config.read(self.mailingPropertyPath)
        return config["DEFAULT"]["SMTPServer"], config["DEFAULT"]["UserName"], \
            config["DEFAULT"]["Password"], config["DEFAULT"]["Sender"]

    def getAllProjects(self, scriptDir):

        allProjects = []
        allDirs =[os.path.join(scriptDir, d) for d in os.listdir(scriptDir) if os.path.isdir(os.path.join(scriptDir, d))]
        proDirs = [d for d in allDirs if self.propertyFileName in os.listdir(d)]

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
                debug = open(self.projectOutputFile, "w")
                debug.write(str(datetime.now()))
                debug.flush()
                output = subprocess.check_output(project.exucmd.split(" "), stderr=debug)
                debug.write(output.decode("utf-8"))
                debug.close()
                print("Script: %s, excuted successfully!" % (project.name))
            except subprocess.CalledProcessError as e:
                print("Script: %s, return non-zero" % (project.name))
                debug.write(e.output.decode("utf-8"))
                debug.close()
                failProjects.append(project)

        # send mails
        if len(failProjects) > 0:
            for project in failProjects:
                print()
                print("=" * 60)
                print(
                    "Handle failed protject: %s\n sending mail..." %
                    project.name)
                self.handleFailProject(project)
                print("=" * 60)

    def handleFailProject(self, project):
        """
        sendFiles = project.sendFile
        sendFiles.append(self.projectOutputFile)
        sendFiles = list(
            map(lambda f: os.path.join(project.path, f), sendFiles))
        for sendFile in sendFiles:
            if not os.path.exists(sendFile):
                # not found sendingFile
                err = " Posting file can not be found: %s"\
                    % os.path.basename(sendFile)
                print(err)
                print(" sending err to maintainer...")
                self.sendMail(
                    project.maintainer,
                    subject=project.name,
                    msg=err,
                    fileList=[
                        os.path.join(
                            project.path,
                            self.projectOutputFile)]
                )

                print(" finish sending, return")

                # skip the rest of actions
                return
        """

        self.sendMail(
            msg="""
            %s Script return non-zero <br>
            see workspace <a href="https://ci.deepin.io/job/AutoScript/ws/Script/%s">
            %s workspace</a>
            """ % (project.name, os.path.basename(project.path), project.name),
            subject=project.name,
            receiver=project.cclist
            )

    def sendMail(
            self, receiver, msg="", subject="", sender=None, fileList=[]):

        if sender is None:
            sender = self.sender

        # collect the attach
        msgRoot = MIMEMultipart("alternative")
        msgRoot["Subject"] = "%s: %s" % (self.subjectPrefix, subject)

        # attach msg
        msgPart = MIMEText("%s%s" %(msg, "<br>"), "html", "utf-8")
        msgRoot.attach(msgPart)

        # attache file
        for sendFile in fileList:
            with open(sendFile) as f:
                att = MIMEText(f.read(), "base64", "utf-8")
            att["Content-Type"] = "application/octet-stream"
            att["Content-Disposition"] = 'attachment; filename="%s"'\
                % os.path.basename(sendFile)
            msgRoot.attach(att)

        footer = """
        <br><hr>
        <footer>
          <br>
          <p>Posted by: <a href="https://ci.deepin.io/job/AutoScript/">ci.deepin.io/job/AutoScript</a></p>
          <p>Contact information: <a href="mailto:tangcaijun@linuxdeepin.com">tangcaijun@linuxdeepin.com</a></p>
        </footer>
        """
        signPart = MIMEText(footer, "html", "utf-8")
        msgRoot.attach(signPart)

        try:
            smtp = self.getMailingServiceInstance()
            smtp.sendmail(self.sender, receiver, msgRoot.as_string())
            smtp.quit()
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused)\
               as e:
            print(e)
            raise e
        """
            print("try to connect again ... ")
            if not self.readyMailingService(self.smtpserver, self.username, self.password):
                print("can not connect to mailing server, abort.")
                raise e
                quit(1)
            self.smtp.sendmail(self.sender, receiver, msgRoot.as_string())
        """

        print(" mailing successfully")


if __name__ == "__main__":
    autoscript = AutoScript()
