#!/usr/bin/env python3
# coding=utf-8

import sqlite3

import subprocess
import os
import sys

class AutoSoftwareCenter(object):

    """
    AutoSoftwareCenter
       Auto check the package sync between software center and official base
        this must be run in a machine with a official source_list
    """

    def __init__(self, packagesFilesListPath, outputDir):

        # clean workspace
        #self.readyWorkSpace()

        self.packagesFilesListPath = packagesFilesListPath
        self.allValidPackages = self.getAllValidPackages(self.packagesFilesListPath)

        # map:  database => tables
        self.databases = {
            "db/software/software.db": (
                "software",)}

        """
        self.databases = {
            "db/desktop/desktop2014.db": (
                "package",),
            "db/software/software.db": (
                "software",)}
        """

        self.recordFile = open("%s.rd" % os.path.join(outputDir, os.path.basename(self.packagesFilesListPath)), "w")

        self.unmetPkgs = set()

        self.check_database()

        self.recordFile.close()

        # clean work space
        #self.cleanWorkSpace()

        """
        if len(self.unmetPkgs) > 0:
            # trigger the mailing event
            quit(1)

        quit(0)
        """

    def readyWorkSpace(self):
        try:
            subprocess.call(["bash", "BeforeRun.sh"])
        except Exception as e:
            #raise e
            print(e)

    def getAllValidPackages(self, listsPath):
        allValidPackages = set()
        packageFiles = [f for f in os.listdir(listsPath)\
                        if f.endswith("Packages")]
        for packageFile in packageFiles:
            packageFile = os.path.join(listsPath, packageFile)
            #print(packageFile)
            with open(packageFile) as f:
                packageName = ""
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    if line.startswith("Package: "):
                        packageName = line.split("Package: ")[1].strip()
                    if line.startswith("Architecture: "):
                        arch = line.split("Architecture: ")[1].strip()
                        # all
                        if arch == "all":
                            packageNameI386 = packageName + ":i386"
                            allValidPackages.add(packageNameI386)
                            packageNameAmd64 = packageName + ":amd64"
                            allValidPackages.add(packageNameAmd64)
                        # amd64 or i386
                        packageName += ":" + arch
                        allValidPackages.add(packageName)
        return allValidPackages


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
                    # i386
                    if pkgName.endswith(":i386") and \
                       pkgName not in self.allValidPackages:
                        self.unmetPkgs.add(pkgName)
                    # amd64
                    elif pkgName.endswith(":amd64") and \
                            pkgName not in self.allValidPackages:
                        self.unmetPkgs.add(pkgName)
                    # all
                    else:
                        pkgNameAmd64 = pkgName + ":amd64"
                        if pkgNameAmd64 not in self.allValidPackages:
                            pkgNameI386 = pkgName + ":I386"
                            if pkgNameI386 not in self.allValidPackages:
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
            print(e)
            #raise e
            pass

if __name__ == "__main__":
    pass
    #path = "/home/choldrim/SRC/PYTHON/DeepinSoftwareCenter/PackageLists/北京交通大学"
    #path = "/home/choldrim/SRC/PYTHON/DeepinSoftwareCenter/PackageLists/Piotrkosoft.net (http)/"
    path = sys.argv[1]
    asc = AutoSoftwareCenter(path)
