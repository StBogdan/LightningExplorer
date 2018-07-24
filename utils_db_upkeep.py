# Script for adding new dates into the Postgres database
# For website visualisation
# Bogdan Stoicescu (bs5017)

import os,django
import json
from datetime import datetime
from datetime import timedelta
from utils_databasePopulate import *
import utils_metrics as metrics
#Setup django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
# django.setup()
# from nodes.models import *
# data_location = open('/etc/lndmon_data_location.txt').read().strip()


def db_put_metrics(metric_filenames,file_path_prefix):
    for metric_file in metric_filenames:
        # os.getcwd()+os.sep +
        imageSource =  file_path_prefix + os.sep+ metric_file
        metric_title, metric_desc, metric_dataset_url,metric_dataset_type = metrics.get_metric_info(metric_file)
        metric_dataset_options = "options: { scales: { xAxes: [{ type: 'time' }] }}"

        newMetric = Metric(
                            title =metric_title,
                            description=metric_desc,
                            dataset_type= metric_dataset_type,
                            dataset_options= metric_dataset_options,
                            dataset_url =metric_dataset_url,
                            image_url = imageSource)
        newMetric.save()
        print("Put metric in database")

def db_update_metrics():
    db_put_metrics(os.listdir("media"),"media")


def getLastDate():
    try:
        last_date= Node.objects.all().values("date_logged").first()["date_logged"].strftime("%Y-%m-%d")
    except:
        last_date="No dates logged"
    return

def getCurrentDate(time_offset = timedelta()):
    return (datetime.now() - time_offset).strftime("%Y-%m-%d")

def getMetricList():
    #look in the db, grab all metrics and get their name (cut off the "media/" prefix)
    return [ x["image_url"].split("/")[1].replace(".png","") for x in  Metric.objects.all().values("image_url")]


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

def dataset_update(metric_list):
    data_set = metrics.process_dataset(data_location)
    print("Got metric list:\t"+ str(metric_list))
    for metric in metric_list:
        metrics.generate_and_save(metric,data_set)
    print("Updated datasets")

# Last day's data should be in own folder
#Update by putting the last day in
# data_update(getCurrentDate(timedelta(days=1)))
if __name__ == "__main__":
    if(len(getMetricList()) == 0):
        db_update_metrics()
    dataset_update(getMetricList())
