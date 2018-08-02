# Script for adding new dates into the Postgres database
# For website visualisation
# Bogdan Stoicescu (bs5017)

import os,django
import json
from datetime import datetime
from datetime import timedelta
from utils_databasePopulate import *
import utils_metrics as metrics
import utils_IP as ip
import sys
#Setup django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
# django.setup()
# from nodes.models import *
data_location = open('/etc/lndmon_data_location.txt').read().strip()


def db_put_metrics(metric_filenames,file_path_prefix):
    for metric_file in metric_filenames:
        # os.getcwd()+os.sep +
        print("Putting metric in database:\t"+ metric_file)

        imageSource =  file_path_prefix + os.sep+ metric_file
        metric_dict = metrics.get_metric_info(metric_file)
        newMetric = Metric(
                            title       = metric_dict["title"],
                            description = metric_dict["description"],
                            dataset_type= metric_dict["dataset_type"],
                            dataset_options= metric_dict["dataset_options"],
                            dataset_url    = metric_dict["dataset_url"],
                            dataset_labels = metric_dict["dataset_labels"],
                            image_url      = metric_dict["image_url"])
        newMetric.save()

def db_update_metrics():
    db_put_metrics(os.listdir("media"),"media")

def db_reset_metrics():
    print("Removing all metrics currently in database")
    Metric.objects.all().delete()

def get_last_logged_date():
    try:
        last_date= Node.objects.all().values("date_logged").first()["date_logged"].strftime("%Y-%m-%d")
    except:
        last_date="No dates logged"
    return last_date

def get_current_date(time_offset = timedelta()):
    return (datetime.now() - time_offset).strftime("%Y-%m-%d")

def get_metric_list():
    #look in the db, grab all metrics and get their name (cut off the "media/" prefix)
    return [ x for x in json.loads(open("metric_dict.json").read())]

def get_date_data(target_date):
    print(get_last_logged_date())
    print("Get date data in:\t" + data_location + os.sep + target_date)
    datafiles = os.listdir(data_location + os.sep + target_date)
    first_file = [x for x in datafiles if x.endswith(".graph")][0]
    file_path = data_location + os.sep + target_date+ os.sep + first_file
    return file_path

def ip_map_update(target_date):
    file_fpath = get_date_data(target_date)
    ip_poz_dict = ip.create_ip_dict(file_fpath)
    results_file = open("datasets/ip_location_data","w+")
    results_file.write(json.dumps(ip_poz_dict))
    results_file.close()

def add_new_day(target_date): #Date is YYYY-MM-DD format string
    try:
        #Get the first file (.graph will be before .netinfo)
        file_path= get_date_data(target_date)
        print("Got target file:\t"+ file_path)
        date,nodes,chans = getNetworkData(file_path)

        node_extra_info = [getCapacity(node["pub_key"],chans) for node in nodes]
        nodes_entries, address_entries = createNodeEntries(nodes,date,[ x for [x,y] in node_extra_info ] , [ y for [x,y] in node_extra_info ] )

        edges_entries, policies = createChanEntries(chans,date,nodes_entries)

        print("Created entries for "+ str(len(nodes_entries)) + " nodes and " + str(len(edges_entries)) + " channels " + " date:" + date.strftime("%Y-%m-%d %H:%M:%S") )
    except Exception as e:
        print("ERROR ON DATE: " + target_date + " \t" + str(e))

def data_update(full_date = get_current_date() ):
   if(get_last_logged_date() != full_date ):
       print("Adding day in databaset:\t" + str(full_date))
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
# Update by putting the last day in
# data_update(get_current_date(timedelta(days=1)))
if __name__ == "__main__":
    print("[Server Upkeep][1/5] Updating IP database")
    ip_map_update(get_last_logged_date())     # Update IP map

    print("[Server Upkeep][2/5] Updating website database")
    data_update()     #Put new day in db

    #Option for reseting metrics
    if(len(sys.argv) > 1 and sys.argv[1] == "reset"):
        print("[Server Upkeep][Reset] Resetting metrics")
        db_reset_metrics()

    #Check metric presence
    print("[Server Upkeep][3/5] Checking metric presence")
    if(len(get_metric_list()) == 0):
        db_update_metrics()

    print("[Server Upkeep][4/5] Updating datasets for metrics")
    #Update datasets used by metrics
    dataset_update(get_metric_list())
