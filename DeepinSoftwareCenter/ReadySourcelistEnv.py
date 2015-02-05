#!/usr/bin/env python3
# coding=utf-8

from urllib import request
from urllib.error import HTTPError
import gzip
import os

class SourcelistObject(object):
    def __init__(self, sourceLine):
        (self.url, self.codeName, self.components) = self.parse(sourceLine)
        
    def parse(self, sourceLine):
        items = [i for i in sourceLine.split(" ") if len(i) > 0]
        if len(items) < 4:
            print("fuck~~~")
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
            amd64PackageFileUrl = "%s/dists/%s/%s/binary-amd64/Packages.gz" % \
                    (self.url, self.codeName, comp)
            i386PackageFileUrl = "%s/dists/%s/%s/binary-i386/Packages.gz" % \
                    (self.url, self.codeName, comp)
            packageFilesUrl.append(amd64PackageFileUrl)
            packageFilesUrl.append(i386PackageFileUrl)
            
        return packageFilesUrl

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

from aptsources import distro
import configparser
def genAllSourcelists():
    codeName = distro.get_distro().codename
    for mirror in os.listdir("Mirrors"):
        if not mirror.endswith(".ini"):
            continue
        config = configparser.ConfigParser()
        filePath = os.path.join(os.path.join(os.getcwd(), "Mirrors"), mirror)
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

        sourcePath = os.path.join(os.getcwd(), \
                                  os.path.join("Sourcelists", sourceName))
        with open(sourcePath, "w") as f:
            f.write(sourceContent) 

def getAllSourcelist():
    sourceListPaths = os.listdir("Sourcelists")
    sourceListPaths = [os.path.join(os.path.join(os.getcwd(), "Sourcelists"),\
                                    p) for p in sourceListPaths ]
    return sourceListPaths
    

def genPackageFiles(sourcelistPath):

    with open(sourcelistPath) as f:
        data = f.read()

    lines = [l for l in data.split("\n") if len(l) > 0 and not l.startswith("#")]

    packageFilesUrl = []
    for line in lines:
        slo = SourcelistObject(line)
        packageFilesUrl.append(slo.getAllPackageFilesUrl())

    path = os.path.join(os.path.join(os.getcwd(), "PackageLists"), \
                       os.path.basename(sourcelistPath))
    print("store package file lists in :", path)
    if not os.path.exists(path):
        os.makedirs(path)

    for sourceGroup in packageFilesUrl:
        for packageFileUrl in sourceGroup:
            try:
                print("ready:%s" % packageFileUrl)
                with request.urlopen(packageFileUrl) as response:
                    data = response.read()

                filePath = os.path.join(path, \
                        packageFileUrl.split("http://")[1].replace("/", "_"))
                with open(filePath, "wb") as f:
                    f.write(data)
 
                with gzip.open(filePath, "rt") as gz:
                    with open(filePath.split(".gz")[0], "w") as f:
                        f.write(gz.read())
            except HTTPError as e:
                print(e)
                print(packageFileUrl)

    # clean
    for fileName in os.listdir(path):
        if fileName.endswith(r".gz"):
            os.remove(os.path.join(path, fileName))

from AutoSoftwareCenter import AutoSoftwareCenter
def readySourceListEnv():
    genAllSourcelists()
    for sourcelistPath in getAllSourcelist():
        genPackageFiles(sourcelistPath)
        pkgListsPath = os.path.join(os.path.join(os.getcwd(), "PackageLists"),\
                                    os.path.basename(sourcelistPath))
        print("call AutoSoftwareCenter with: %s" % pkgListsPath)
        asc = AutoSoftwareCenter(pkgListsPath)



if __name__ == '__main__':
    readySourceListEnv()
    

