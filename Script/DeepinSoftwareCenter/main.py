#!/usr/bin/env python3
# coding=utf-8

import subprocess

import ReadySourcelistEnv as ready
import ReadyDatabase as db


def readyWorkSpace():
    try:
        subprocess.call(["bash", "BeforeRun.sh"])
    except Exception as e:
        #raise e
        print(e)

def cleanWorkSpace():
    try:
        subprocess.call(["bash", "AfterRun.sh"])
    except Exception as e:
        print(e)
        #raise e
        pass


if __name__ == "__main__":
    
    readyWorkSpace()

    db.readyDatabase()
    ready.readySourceListEnv()
    print("finish all checking")

    cleanWorkSpace()

    # trig the mailing event
    quit(1)
