#!/usr/bin/env python3
# coding=utf-8

import os
import configparser
import subprocess
import smtplib

from datetime import datetime

from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText


class Project(object):

    def __init__(self, name, path, exucmd, **args):
            #maintainer=None, cclist=None, period=None, sendFile=None, resultDir=None, args):
        self._name = name.strip()
        self._path = path.strip()
        self._exucmd = exucmd.strip()
        self._maintainer = args.get("maintainer", "").strip()
        self._cclist = [cc.strip() for cc in args.get("ccList", "").split(",") if len(cc.strip()) > 0]
        self._period = args.get("period", "").strip()
        self._sendFile = [f.strip() for f in args.get("sendFile", "").split(",") if len(f.strip()) > 0]
        self._resultDir = [d.strip() for d in args.get("resultDir", "").split(",") if len(d.strip()) > 0]

        self.mailingHowever = args.get("mailingHowever", "0")
        self.mailingOnFail = args.get("mailingOnFail", "0")
        self.cleanFile = [f.strip() for f in args.get("cleanFile", "").split(",") if len(f.strip()) > 0]
        self.fileToMailingContent = [f.strip() for f in args.get("fileToMailingContent").split(",") if len(f.strip()) > 0]
        self.mailingSubject = args.get("mailingSubject", "AutoScript").strip()

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
    def resultDir(self):
        return self._resultDir

    @resultDir.setter
    def resultDir(self, value):
        self._resultDir = value

    @property
    def outputLog(self):
        return self._outputLog

    @outputLog.setter
    def outputLog(self, value):
        self._outputLog = value


class AutoScript(object):

    def __init__(self):

        self.configs = {}

        # mailing property
        self.mailingPropertyPath = os.path.join(os.getenv("HOME"), ".AutoScriptConfig/MailingProperty.ini")
        if not os.path.exists(self.mailingPropertyPath):
            self.mailingPropertyPath = os.path.join(os.getcwd(), "MailingProperty.ini")

        (self.smtpserver, self.username, self.password, self.sender) = self.getMailingProperty()

        self.subjectPrefix = "Deepin-CI/AutoScript"


        # init projects
        self.propertyFileName = "AUTO.ini"
        self.scriptDir = os.path.join(os.getcwd(), "Script")
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
            config["DEFAULT"]["Password"], config["DEFAULT"]["UserName"]

    def getAllProjects(self, scriptDir):

        """
        init all valid projects
        """
        allProjects = []
        allDirs =[os.path.join(scriptDir, d)
                  for d in os.listdir(scriptDir) if os.path.isdir(os.path.join(scriptDir, d))]
        proDirs = [d for d in allDirs if self.propertyFileName in os.listdir(d)]

        for proDir in proDirs:

            proName = os.path.basename(proDir)

            if self.getProConfValue(proName, "SYSTEM", "Enable") != "1":
                continue

            project = Project(self.getProConfValue(proName, "DEFAULT", "Name"),
                    proDir,
                    self.getProConfValue(proName, "DEFAULT", "EXUCMD"),
                    maintainer = self.getProConfValue(proName, "DEFAULT", "Maintainer"),
                    ccList = self.getProConfValue(proName, "DEFAULT", "CCList"),
                    period = self.getProConfValue(proName, "DEFAULT", "Period"),
                    sendFile = self.getProConfValue(proName, "DEFAULT", "SendFile"),
                    resultDir = self.getProConfValue(proName, "DEFAULT", "ResultDir"),
                    mailingHowever = self.getProConfValue(proName, "DEFAULT", "MailingHowever"),
                    mailingOnFail = self.getProConfValue(proName, "DEFAULT", "MailingOnFail"),
                    cleanFile = self.getProConfValue(proName, "DEFAULT", "CleanFile"),
                    fileToMailingContent = self.getProConfValue(proName, "DEFAULT", "FileToMailingContent"),
                    mailingSubject = self.getProConfValue(proName, "DEFAULT", "MailingSubject")
                    )

            allProjects.append(project)

        return allProjects


    def getProConfValue(self, proName, section, key, default=""):

        if not self.configs.get(proName):
            self.configs[proName] = configparser.ConfigParser()
            self.configs[proName].read("%s/%s/%s" % (self.scriptDir, proName, self.propertyFileName))

        return self.configs[proName].get(section, key, fallback="")


    def work(self, allProjects):

        failProjects = []
        successProjects = []
        for project in allProjects:
            print("cmd:", project.exucmd)

            # change to sub project dir
            os.chdir(project.path)

            try:

                debug = open(self.projectOutputFile, "w")
                debug.write("___AutoScript -- %s___\n" % (str(datetime.now())))
                debug.flush()
                print ("EXUCMD: ", project.exucmd)
                output = subprocess.check_output(project.exucmd.split(" "), stderr=debug)
                debug.write(output.decode("utf-8"))
                debug.close()
                print("Script: %s, excuted successfully!" % (project.name))
                successProjects.append(project)

            except subprocess.CalledProcessError as e:

                print("Script: %s, return non-zero" % (project.name))
                debug.write(e.output.decode("utf-8"))
                debug.close()
                failProjects.append(project)

        # send mails
        for project in successProjects:
            if project.mailingHowever:
                print()
                print("=" * 60)
                print( "Handle success protject: %s\n sending mail..." % project.name)
                self.handleSuccessProject(project)
                print("=" * 60)

        for project in failProjects:
            if project.mailingHowever or project.mailingOnFail:
                print()
                print("=" * 60)
                print( "Handle failed protject: %s\n sending mail..." % project.name)
                self.handleFailProject(project)
                print("=" * 60)

        # clean the files those need to be cleaned
        for project in successProjects + failProjects:
            self.cleanTheCleanedFile(project)


    def handleSuccessProject(self, project):

        fileList = []
        #fileList.append(os.path.join(project.path, self.projectOutputFile))
        sendFileList = [os.path.join(project.path, f) for f in project.sendFile]
        fileList += sendFileList

        workspacesStr = ""
        for d in project.resultDir:
            item = """<br><a href="https://ci.deepin.io/job/AutoScript/ws/Script/%s/%s">
            %s/%s</a>""" % (os.path.basename(project.path), d, os.path.basename(project.path), d)
            workspacesStr += item

        if project.fileToMailingContent:
            msg = ""
            for f in project.fileToMailingContent:
                if os.path.exists(f):
                    with open(f) as fp:
                        msg += fp.read()
                        msg += "<p>"
        else:
            msg = """ %s script has been completed, <br> check it on jenkins: %s """ % (project.name, workspacesStr)

        now = datetime.now()
        dateStr = "%d-%d-%d" %(now.year, now.month, now.day)
        subject = "%s(%s)" % (project.mailingSubject, dateStr)

        self.sendMail(msg=msg, subject=subject, receiver=project.cclist, fileList=fileList)

    def handleFailProject(self, project):

        fileList = []
        sendFileList = [os.path.join(project.path, f) for f in project.sendFile]
        fileList += sendFileList

        workspacesStr = ""
        for dir in project.resultDir:
            item = """<br><a href="https://ci.deepin.io/job/AutoScript/ws/Script/%s/%s">
            %s/%s</a>""" % (os.path.basename(project.path), dir,
                             os.path.basename(project.path), dir)
            workspacesStr += item

        if project.fileToMailingContent:
            msg = ""
            for f in project.fileToMailingContent:
                if os.path.exists(f):
                    with open(f) as fp:
                        msg += fp.read()
                        msg += "<p>"
        else:
            msg = """ %s Script return non-zero <br> check it on jenkins: %s """ % (project.name, workspacesStr)

        now = datetime.now()
        dateStr = "%d-%d-%d" %(now.year, now.month, now.day)
        subject = "%s(%s)" % (project.mailingSubject, dateStr)

        self.sendMail(msg=msg, subject=subject, receiver=project.cclist, fileList=fileList)


    def sendMail( self, receiver, msg="", subject="", sender=None, fileList=[]):

        if sender is None:
            sender = self.sender

        # collect the attach
        msgRoot = MIMEMultipart("alternative")
        #msgRoot["Subject"] = "%s: %s" % (self.subjectPrefix, subject)
        msgRoot["Subject"] = "%s" % (subject)

        # attach msg
        msgPart = MIMEText("%s%s" %(msg, "<br>"), "html", "utf-8")
        msgRoot.attach(msgPart)

        # attache file
        for sendFile in fileList:
            print ("send file: ", sendFile)
            att = MIMEBase("application", "zip")
            with open(sendFile, "rb") as f:
                att.set_payload(f.read())
            encoders.encode_base64(att)
            att["Content-Disposition"] = 'attachment; filename="%s"' % os.path.basename(sendFile)
            msgRoot.attach(att)

        footer = """
        <br><hr>
        <footer>
          <br>
          <p>Posted by: <a href="https://ci.deepin.io/job/AutoScript/">deepin ci AutoScript</a></p>
          <p>Contact: <a href="mailto:tangcaijun@linuxdeepin.com">tangcaijun@linuxdeepin.com</a></p>
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

        print(" mailing successfully")


    def cleanTheCleanedFile(self, project):

        cleanedFile = [os.path.join(project.path, f) for f in project.cleanFile]
        rmCmd = "rm -rf %s" % " ".join(cleanedFile)
        print ("clean files cmd: ", rmCmd)
        os.system(rmCmd)


if __name__ == "__main__":
    autoscript = AutoScript()
