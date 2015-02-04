#!/usr/bin/env python3
# coding=utf-8

import apt
import apt_pkg
import sqlite3
from urllib import request

import subprocess
import tarfile
import os

class AutoSoftwareCenter(object):

    """
    AutoSoftwareCenter
       Auto check the package sync between software center and official base
        this must be run in a machine with a official source_list
    """

    def __init__(self):

        self.deepinSCVersion = "3.0.1+20141230125726~0565641e10"
        self.deepinSCUrl = "http://packages.linuxdeepin.com/deepin/pool/main/d/deepin-software-center-data/deepin-software-center-data_%s.tar.gz" % self.deepinSCVersion

        # clean workspace
        #self.readyWorkSpace()

        self.apt_cache = apt.cache.Cache()
        self.pkg_cache = apt_pkg.Cache()

        # get and un-tar the newest software-center-database
        self.readyDatabase()

        # map:  database => tables
        self.databases = {
            "db/desktop/desktop2014.db": (
                "package",),
            "db/software/software.db": (
                "software",)}

        self.recordFile = open("DeepinSC-Missed-Pkgs.log", "w")
        self.unmetPkgs = set()

        self.check_database()

        self.recordFile.close()

        # clean work space
        self.cleanWorkSpace()

        if len(self.unmetPkgs) > 0:
            # trigger the mailing event
            quit(1)

        quit(0)

    def readyWorkSpace(self):
        try:
            subprocess.call(["bash", "BeforeRun.sh"])
        except Exception as e:
            #raise e
            pass

    def readyDatabase(self):
        try:
            #subprocess.check_output(
            #    ["apt-get", "source", "deepin-software-center-data"])
            #verStr = self.apt_cache[
            #    "deepin-software-center-data"].candidate.version
            response = request.urlopen(self.deepinSCUrl)
            data = response.read()
            response.close()
            fileName = "deepin-software-center-data.tar.gz"
            with open(fileName, "wb") as f:
                f.write(data)

            # tar download file
            with tarfile.open(fileName) as tar:
                tar.extractall()

            # extract the database
            dbPath = os.path.join(
                os.getcwd(),
                "deepin-software-center-data-" +
                self.deepinSCVersion)
            dbPath = os.path.join(os.path.join(dbPath, "data"), "origin")

            with tarfile.open(os.path.join(dbPath, "dsc-software-data.tar.gz")) as tar:
                tar.extract("software/software.db", "db/")

            with tarfile.open(os.path.join(dbPath, "dsc-desktop-data.tar.gz")) as tar:
                tar.extract("desktop/desktop2014.db", "db/")

        except request.URLError as e:
            print("Can't get software-center-data, abort.")
            print("Err:\n %s" % e.output)
            raise e

    def check_database(self):
        for dbName in self.databases:
            conn = sqlite3.connect(dbName)
            cursor = conn.cursor()
            for tableName in self.databases[dbName]:
                sql = "select pkg_name from %s;" % tableName
                cursor.execute(sql)
                pkgNames = cursor.fetchall()
                print("%s packages: %d" % (dbName, len(pkgNames)))
                for pkgName in pkgNames:
                    pkgName = pkgName[0]
                    if pkgName not in self.apt_cache:
                        # check if there is 32bit pkg
                        if not pkgName.endswith(":i386"):
                            if pkgName + ":i386" in self.apt_cache:
                                continue
                        #print (pkgName)
                        self.unmetPkgs.add(pkgName)
        print("all unmet packages: %d" % len(self.unmetPkgs))
        for name in self.unmetPkgs:
            self.record(name)

    def record(self, pkgName):
        data = "%s\n" % pkgName
        self.recordFile.write(data)

    def cleanWorkSpace(self):
        try:
            subprocess.call(["bash", "AfterRun.sh"])
        except Exception as e:
            #raise e
            pass

if __name__ == "__main__":
    asc = AutoSoftwareCenter()
