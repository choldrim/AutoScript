#!/usr/bin/env python3
# coding=utf-8

import configparser
import gzip
import hashlib
import os
import logging

from urllib import request
from urllib.error import HTTPError, URLError


packagesListDir = os.path.join(os.getcwd(), "PackagesFilesList")
sourceslistDir = os.path.join(os.getcwd(), "SourcesList")
mirrorsListDir = os.path.join(os.getcwd(), "MirrorsList")
#outputDir = os.path.join(os.getcwd(), "Output")
outputDir = os.path.join(os.getcwd(), "CheckedResult")

if not os.path.exists(packagesListDir):
    os.makedirs(packagesListDir)

if not os.path.exists(sourceslistDir):
    os.makedirs(sourceslistDir)

if not os.path.exists(mirrorsListDir):
    os.makedirs(mirrorsListDir)

if not os.path.exists(outputDir):
    os.makedirs(outputDir)


logging.basicConfig(level=logging.DEBUG,
                   format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s",
                   datefmt="%d %b %Y %H:%M:%S", 
                   filename="DEBUG.LOG",
                   filemode="w")

class SourcelistObject(object):
    def __init__(self, sourceLine):
        (self.url, self.codeName, self.components) = self.parse(sourceLine)
        
    def parse(self, sourceLine):
        items = [i for i in sourceLine.split(" ") if len(i) > 0]
        if len(items) < 4:
            print("fuck source list~~~")
            print(sourceLine)
            quit(1)
        url = items[1]
        if url.endswith("/"):
            url = url[:-1]
        codeName = items[2]
        components = items[3:]
        
        return url, codeName, components
    
    def getAllPackageFilesUrl(self):
        packageFilesUrl = []
        for comp in self.components:
            # url + dist + codename + component
            amd64PackageFileUrl = "%s/dists/%s/%s/binary-amd64/Packages" % \
                    (self.url, self.codeName, comp)
            i386PackageFileUrl = "%s/dists/%s/%s/binary-i386/Packages" % \
                    (self.url, self.codeName, comp)
            packageFilesUrl.append(amd64PackageFileUrl)
            packageFilesUrl.append(i386PackageFileUrl)
            
        return packageFilesUrl

    # map: packageFileUrl => md5Sum
    def getMd5sumMap(self): 
        try:
            print("getting md5 sums from release files:")
            md5SumsMap = {}
            codeNameUrl = "%s/dists/%s" % (self.url, self.codeName)
            releaseFileUrl = "%s/Release" % codeNameUrl
            print(releaseFileUrl)
            response = request.urlopen(releaseFileUrl)
            data = response.read().decode("utf-8")
            # filter other sum, like sha1...
            data = data[data.index("MD5Sum:"):data.index("SHA1:")]
            response.close()
            for line in data.split("\n"):
                if line.startswith(" ") and line.endswith("Packages"):
                    items = [x for x in line.split(" ") if len(x) > 0]
                    if len(items) != 3:
                        continue
                    md5sum = items[0]
                    url = "%s/%s" % (codeNameUrl, items[2])
                    key = url.split("http://")[1].replace("/", "_")
                    if key in md5SumsMap:
                        continue
                    md5SumsMap[key] = md5sum
            #print(md5SumsMap)
            return md5SumsMap
        except URLError as e:
            estr = "err: %s, url: %s" %(str(e), releaseFileUrl)
            print(estr)
            logging.error(estr)

        except HTTPError as e:
            estr = "err: %s, url: %s" %(str(e), releaseFileUrl)
            print(estr)
            logging.error(estr)

        except Exception as e:
            estr = "err: %s, url: %s" %(str(e), releaseFileUrl)
            print(estr)
            logging.error(estr)
            raise e


ubuntu_source_content_template = [
"deb %s %s main restricted universe multiverse",
"deb %s %s-security main restricted universe multiverse",
"deb %s %s-updates main restricted universe multiverse",
"# deb %s %s-proposed main restricted universe multiverse",
"# deb %s %s-backports main restricted universe multiverse",
"deb-src %s %s main restricted universe multiverse",
"deb-src %s %s-security main restricted universe multiverse",
"deb-src %s %s-updates main restricted universe multiverse",
"# deb-src %s %s-proposed main restricted universe multiverse",
"# deb-src %s %s-backports main restricted universe multiverse",
]

deepin_source_content_template = [
"deb %s %s main universe non-free",
"deb-src %s %s main universe non-free",
"#deb %s %s-updates main universe non-free",
"#deb-src %s %s-updates main universe non-free",
]

def genAllSourcelists():
    # fuck this in debian machine
    #codeName = distro.get_distro().codename
    codeName = "trusty"

    for mirror in os.listdir(mirrorsListDir):
        if not mirror.endswith(".ini"):
            continue
        config = configparser.ConfigParser()
        filePath = os.path.join(mirrorsListDir, mirror)
        config.read(filePath)
        if "name[zh_CN]" in config["mirror"]:
            sourceName = config["mirror"]["name[zh_CN]"]
        else:
            sourceName = config["mirror"]["name[en_US]"]
        sourceName = sourceName.replace("/", "_")
        ubuntuURL = config["mirror"]["ubuntu_url"]
        deepinURL = config["mirror"]["deepin_url"]
        
        sourceContent = ""
        for line in ubuntu_source_content_template:
            sourceContent += "%s\n" % line % (ubuntuURL, codeName)
        for line in deepin_source_content_template:
            sourceContent += "%s\n" % line % (deepinURL, codeName)

        sourcePath = os.path.join(sourceslistDir, sourceName)
        with open(sourcePath, "w") as f:
            f.write(sourceContent) 

# return the source list which has been generated
def getAllSourcelist():
    sourceListPaths = os.listdir(sourceslistDir)
    sourceListPaths = [os.path.join(sourceslistDir,p)
                       for p in sourceListPaths
                       if os.path.isfile(os.path.join(sourceslistDir,p))
                      ]
    return sourceListPaths
    
from threading import Thread
def genPackageFiles(sourcelistPath):

    # construct packages file list
    with open(sourcelistPath) as f:
        data = f.read()
    lines = [l for l in data.split("\n") if len(l) > 0 and not l.startswith("#")]
    packageFilesUrl = [] # == [[pkgFileUrl, pkgFileUrl..], [pkgFileUrl..], ...]
    md5SumsMap = {}   # url : md5sum
    for line in lines:
        slo = SourcelistObject(line)
        packageFilesUrl.append(slo.getAllPackageFilesUrl())
        md5map = slo.getMd5sumMap()
        if not md5map:  # the release file url might be wrong
            continue
        for (k,v ) in md5map.items():
            md5SumsMap[k] = v

    path = os.path.join(packagesListDir, os.path.basename(sourcelistPath))
    print("store package file lists in :", path)
    if not os.path.exists(path):
        os.makedirs(path)

    for sourceGroup in packageFilesUrl:
        downloadThreads = []
        for packageFileUrl in sourceGroup:
            filePath = os.path.join(path, \
                    packageFileUrl.split("http://")[1].replace("/", "_"))
            print("ready:%s" % packageFileUrl)
            print("check md5sum with file:\n %s" % filePath)
            if os.path.exists(filePath):
                with open(filePath, "rb") as f:
                    md5sum = hashlib.md5(f.read()).hexdigest()
                    key = os.path.basename(filePath)
                    if md5SumsMap[key] == md5sum:
                        print (" package file %s is consistent with server file, don't need to update." % packageFileUrl)
                        continue
                    else:
                        print("md5sum is not consistent, update file...")
            else:
                print("package file not exits, download file ... ")

            t = Thread(target=downloadThread, args=(packageFileUrl, filePath,))
            downloadThreads.append(t)
            print("start a download new thread...")
            t.start()

        for t in downloadThreads:
            t.join()

    # clean
    for fileName in os.listdir(path):
        if fileName.endswith(r".gz"):
            os.remove(os.path.join(path, fileName))

        """
            # download packages.gz
            packageGZFileUrl = packageFileUrl + ".gz"
            with request.urlopen(packageGZFileUrl) as response:
                data = response.read()

            # store zip file
            # packages.gz file path
            fileGZPath = filePath + ".gz"
            with open(fileGZPath, "wb") as f:
                f.write(data)

            # unzip
            with gzip.open(fileGZPath, "rt") as gz:
                with open(filePath, "w") as f:
                    f.write(gz.read())

        except HTTPError as e:
            print(e)
            print(packageGZFileUrl)
        """
    
def downloadThread(url, filePath):
    try:
        packageFileUrl = url

        # download packages.gz
        packageGZFileUrl = packageFileUrl + ".gz"
        with request.urlopen(packageGZFileUrl) as response:
            data = response.read()

        print("finish download package file: %s " % packageFileUrl)

        # store zip file
        # packages.gz file path
        fileGZPath = filePath + ".gz"
        with open(fileGZPath, "wb") as f:
            f.write(data)

        # unzip
        with gzip.open(fileGZPath, "rt") as gz:
            with open(filePath, "w") as f:
                f.write(gz.read())

    except HTTPError as e:
        estr = "err: %s, url: %s" % (str(e), packageGZFileUrl)
        print(estr)
        logging.error(estr) 

    except Exception as e:
        estr = "err: %s, url: %s" % (str(e), packageGZFileUrl)
        print(estr)
        logging.error(estr) 


from multiprocessing import Process
from AutoSoftwareCenter import AutoSoftwareCenter
def checkerProcess(sourcelistPath):
    genPackageFiles(sourcelistPath)
    pkgListsPath = os.path.join(packagesListDir, 
                                os.path.basename(sourcelistPath))

    print("call AutoSoftwareCenter with: %s" % pkgListsPath)
    asc = AutoSoftwareCenter(pkgListsPath, outputDir)


def readySourceListEnv():
    genAllSourcelists()
    checkerProcesses = []
    for sourcelistPath in getAllSourcelist():
        p = Process(target=checkerProcess, args=(sourcelistPath, ))
        print("start checker process...")
        p.start()
        checkerProcesses.append(p)

    for p in checkerProcesses:
        p.join()


if __name__ == '__main__':
    readySourceListEnv()
    

