#!/usr/bin/env python3
# coding=utf-8

import apt
import apt_pkg
import sqlite3
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

        self.cleanWorkSpace()

        if len(self.unmetPkgs) > 0:
            # trigger the mailing event
            quit(1)

        quit(0)

    def readyDatabase(self):
        try:
            subprocess.check_output(
                ["apt-get", "source", "deepin-software-center-data"])
            verStr = self.apt_cache[
                "deepin-software-center-data"].candidate.version
            dbPath = os.path.join(
                os.getcwd(),
                "deepin-software-center-data-" +
                verStr)
            dbPath = os.path.join(os.path.join(dbPath, "data"), "origin")

            with tarfile.open(os.path.join(dbPath, "dsc-software-data.tar.gz")) as tar:
                tar.extract("software/software.db", "db/")

            with tarfile.open(os.path.join(dbPath, "dsc-desktop-data.tar.gz")) as tar:
                tar.extract("desktop/desktop2014.db", "db/")

        except subprocess.CalledProcessError as e:
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
            subprocess.call(["bash", "clean.sh"])
        except Exception as e:
            #raise e
            pass

if __name__ == "__main__":
    asc = AutoSoftwareCenter()
