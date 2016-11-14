#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'devjiangzhou'

from sys import argv, exit as esc
from biplist import *
import sys
import os

def enum(**enums):
    return type('Enum', (), enums)
PhaseType = enum(Source="PBXSourcesBuildPhase", Resource="PBXResourcesBuildPhase", Framework='PBXFrameworksBuildPhase')


class PBXFile(object):
    def __init__(self,fileId):
        fileRefId = ROOT[fileId]["fileRef"]
        file = ROOT[fileRefId]
        self.id = fileRefId
        if file["isa"] == "PBXVariantGroup":
            self.name = file["name"]
        elif file["isa"] == "PBXFileReference":
            self.name = file["path"]


class PBXPhase(object):
    def __init__(self,phaseid,isa,dict):
        self.phaseid = phaseid
        files = []
        for phasefileId in dict["files"]:
            file = PBXFile(phasefileId)
            files.append(file)

        self.files = files
        self.isa = isa

class PBXTarget(object):
    def __init__(self,targetId,dict):
        self.targetId = targetId
        self.targetName = dict["name"]
        self.isa = dict["isa"]

        #加载phase
        buildPhases = []
        for phaseId in dict["buildPhases"]:
            phase = ROOT[phaseId]
            isa = phase["isa"]
            if not isa == "PBXShellScriptBuildPhase":
                buildPhase = PBXPhase(phaseId,isa,phase)
                buildPhases.append(buildPhase)

        self.buildPhases = buildPhases

        self.dependencies = dict["dependencies"]
        self.productType = dict["productType"]


class PBXChecker(object):
    def __init__(self,  testTargetName,releaseTargetName):
        self.testTargetName = testTargetName
        self.releaseTargetName = releaseTargetName

        self.releaseTarget = None
        self.testTarget = None

    def check(self):
        def findProjectFile():
            list = os.listdir('.')
            projectFileName = None
            for file in list:
                if file.endswith('.xcodeproj'):
                    projectFileName = file
        
            return projectFileName
        
        filePath = "./%s/project.pbxproj" % findProjectFile()
        
        if not os.path.exists(filePath):
            return None

        os.system("plutil -convert xml1 -o ./project.pbxproj.xml %s" % filePath)

        filePath = "./project.pbxproj.xml"
        global PLIST,ROOT
        PLIST = readPlist(filePath)

        ROOT = PLIST['objects']
        projectID = PLIST["rootObject"]
        targets = ROOT[projectID]["targets"]

        for target in targets:
            dict = ROOT[target]
            targetName = dict["name"]

            if targetName == self.testTargetName:
                self.testTarget = PBXTarget(target,dict)
            elif targetName == self.releaseTargetName:
                self.releaseTarget = PBXTarget(target,dict)

        if not len(self.testTarget.buildPhases) == len(self.releaseTarget.buildPhases):
            print "buildPhase数量不匹配"


        diffs = []
        for testPhase in self.testTarget.buildPhases:
            for releasePhase in self.releaseTarget.buildPhases:
                if testPhase.isa == releasePhase.isa:
                    for testfile in testPhase.files:
                        exist = False
                        for releasefile in releasePhase.files:
                            if testfile.id == releasefile.id and testfile.name == releasefile.name:
                                exist = True

                        if not exist:
                            diffs.append(testfile);

        print '\033[1;31m'
        print '*' * 50
        print '*比对结果'
        print '*' * 50

        if len(diffs) == 0: print "匹配通过"
        else:
            print '\033[1;31m'
            for file in diffs:
                 print '%-100s[匹配不通过]' %file.name


def main():
    checker = PBXChecker(argv[1],argv[2])
    checker.check()

if __name__ == '__main__':
    global PLIST

    if len(argv)<1:
        info='''Input args error, please type: "%(script)s Book_Name_You_Want".'''
        esc(info % { 'script':argv[0] })
    else:
        main()