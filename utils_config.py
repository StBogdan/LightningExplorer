import os
from datetime import datetime
import json
import codecs


site_config = json.loads(codecs.open("/etc/django_config.txt", 'r').read())

def fix_date_string(folderPath = os.getcwd()):
    for fileName in os.listdir(folderPath):
        if(fileName.startswith("2018-") and ( fileName.endswith(".graph") or fileName.endswith(".netinfo")) and fileName.replace(":","-") != fileName): #Check that we are modifying the right files
            print("RENAME:\t"+ fileName + "\t-->\t"+ fileName.replace(":","-"))
            os.rename(folderPath+ os.sep + fileName, folderPath+ os.sep + fileName.replace(":","-"))
        # else:
            # print("RENAME:\tFile " +fileName+ "\tnot eligible for rename")

def fix_dataset(folderPath = os.getcwd()):
    for dayDir in os.listdir(folderPath):
        if(os.path.isdir(dataPath + os.sep + dayDir)):
            print("Fixing folder\t" +dayDir )
            fix_date_string(folderPath+os.sep +dayDir)


def fix_date_string_folder(dataPath):
    for fileName in os.listdir(dataPath):
        if(fileName.startswith("18") and len(fileName) == 6 and os.path.isdir(dataPath + os.sep + fileName)): #Check that we are modifying the right files
            newName = "2018-" + fileName[2:4] + "-" + fileName[4:6]
            print("RENAME:\t"+ fileName + "\t-->\t"+ newName)
            os.rename(os.getcwd()+ os.sep + fileName, os.getcwd()+ os.sep + newName)
        else:
            print("RENAME:\tFile " +fileName+ "\tnot eligible for rename")
