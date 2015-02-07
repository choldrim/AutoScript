#!/usr/bin/env python3
# coding=utf-8

import tarfile
import os

from urllib import request

def readyDatabase():
    # deepinSCVersion = getLastestDSCVersion()
    deepinSCVersion = "3.0.1+20141230125726~0565641e10"
    deepinSCUrl = "http://packages.linuxdeepin.com/deepin/pool/main/d/deepin-software-center-data/deepin-software-center-data_%s.tar.gz" % deepinSCVersion

    print("ready data base")
    print("deepin-software-center version:%s" % deepinSCUrl)

    fileName = "deepin-software-center-data_%s.tar.gz" % deepinSCVersion
    if not os.path.exists(os.path.join(os.getcwd(), fileName)): 
        try:
            response = request.urlopen(deepinSCUrl)
            data = response.read()
            print("finish download")
            response.close()

        except request.URLError as e:
            print("Can't get software-center-data, abort.")
            print("Err:\n %s" % e.output)
            raise e

        with open(fileName, "wb") as f:
            f.write(data)
    else:
        print("file %s is exists, skip download." % fileName)

    # tar download file
    with tarfile.open(fileName) as tar:
        tar.extractall()

    # extract the database
    dbPath = os.path.join(
        os.getcwd(),
        "deepin-software-center-data-" +
        deepinSCVersion)
    dbPath = os.path.join(os.path.join(dbPath, "data"), "origin")

    with tarfile.open(os.path.join(dbPath, "dsc-software-data.tar.gz")) as tar:
        tar.extract("software/software.db", "db/")

    with tarfile.open(os.path.join(dbPath, "dsc-desktop-data.tar.gz")) as tar:
        tar.extract("desktop/desktop2014.db", "db/")

if __name__ == "__main__" :
    readyDatabase()
