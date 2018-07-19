# Script for adding new dates into the Postgres database
# For website visualisation
# Bogdan Stoicescu (bs5017)

import os,django
import json
from datetime import datetime
from utils_databasePopulate import *

#Setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
django.setup()
from nodes.models import *
data_location = open('/etc/lndmon_data_location.txt').read().strip()

def getLastDate():
    try:
        last_date= Node.objects.all().values("date_logged").first()["date_logged"].strftime("%Y-%m-%d")
    except:
        last_date="No dates logged"
    return

def getCurrentDate():
    return datetime.now().strftime("%Y-%m-%d")


def add_new_day(target_date): #Date is YYYY-MM-DD format string
    try:
        #Get the first file (.graph will be before .netinfo)
        datafiles = os.listdir(data_location + os.sep + target_date)
        first_file = [x for x in datafiles if x.endswith(".graph")][0]
        file_path = data_location + os.sep + target_date+ os.sep + first_file
        print("Got target file:\t"+ file_path)
        date,nodes,chans = getNetworkData(file_path)

        node_extra_info = [getCapacity(node["pub_key"],chans) for node in nodes]
        nodes_entries, address_entries = createNodeEntries(nodes,date,[ x for [x,y] in node_extra_info ] , [ y for [x,y] in node_extra_info ] )

        edges_entries, policies = createChanEntries(chans,date,nodes_entries)

        print("Created entries for "+ str(len(nodes_entries)) + " nodes and " + str(len(edges_entries)) + " channels " + " date:" + date.strftime("%Y-%m-%d %H:%M:%S") )
    except Exception as e:
        print("ERROR ON DATE: " + target_date + " \t" + str(e))

def data_update(full_date = getCurrentDate() ):
   if(getLastDate() != full_date ):
       print("Adding day in databaset")
       add_new_day(full_date)
   else:
       print("Current day is in databaset")

data_update()
