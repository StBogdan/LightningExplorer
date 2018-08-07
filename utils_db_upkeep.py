# Script for adding new dates into the Postgres database
# For website visualisation
# Bogdan Stoicescu (bs5017)

import os,django
import json
from datetime import datetime
from datetime import timedelta
import utils_databasePopulate as db_pop
import utils_metrics as metrics
import utils_IP as ip
import sys
from nodes.models import *
#Setup django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
# django.setup()
# from nodes.models import *
data_location= {"testnet": open('/etc/lndmon_data_location.txt').read().strip() , "mainnet":  open('/etc/lndmon_data_location_mainnet.txt').read().strip()}


def db_put_metrics(metric_list):
    for metric_name in metric_list:
        # os.getcwd()+os.sep +
        print("Putting metric in database:\t"+ metric_name)

        metric_dict = metrics.get_metric_info(metric_name,"mainnet")
        mainMetric = Metric(
                            title       = metric_dict["title"],
                            description = metric_dict["description"],
                            dataset_type= metric_dict["dataset_type"],
                            dataset_options= metric_dict["dataset_options"],
                            dataset_url    = metric_dict["dataset_url"],
                            dataset_labels = metric_dict["dataset_labels"],
                            image_url      = metric_dict["image_url"],
                            network      = metric_dict["network"])

        metric_dict_testnet = metrics.get_metric_info(metric_name,"testnet")
        testMetric = Metric(
                            title       = metric_dict_testnet["title"],
                            description = metric_dict_testnet["description"],
                            dataset_type= metric_dict_testnet["dataset_type"],
                            dataset_options= metric_dict_testnet["dataset_options"],
                            dataset_url    = metric_dict_testnet["dataset_url"],
                            dataset_labels = metric_dict_testnet["dataset_labels"],
                            image_url      = metric_dict_testnet["image_url"],
                            network      = metric_dict_testnet["network"])

        mainMetric.save()
        testMetric.save()

def db_update_metrics(): #Create db entries for metric, both mainnet and testnet
    db_put_metrics(get_metric_list())

def db_reset_metrics():
    print("Removing all metrics currently in database")
    Metric.objects.all().delete()

def get_last_logged_date(on_network):
    try:
        last_date= Node.objects.filter(network=on_network).values("date_logged").first()["date_logged"].strftime("%Y-%m-%d")
    except Exception as e:
        print("[Server Upkeep] Failed to get last date:\t"+ str(e))
        last_date="No dates logged"
    return last_date

def get_current_date(time_offset = timedelta()):
    return (datetime.now() - time_offset).strftime("%Y-%m-%d")

def get_metric_list():
    #look in the db, grab all metrics and get their name (cut off the "media/" prefix)
    return [ x for x in json.loads(open("metric_dict.json").read())]

def get_date_data(target_date,network):
    print(get_last_logged_date(network))
    print("Get date data in:\t" + data_location[network] + os.sep + target_date)
    datafiles = os.listdir(data_location[network] + os.sep + target_date)
    first_file = [x for x in datafiles if x.endswith(".graph")][0]
    file_path = data_location[network] + os.sep + target_date+ os.sep + first_file
    return file_path

def ip_map_update(target_date,network):
    file_fpath = get_date_data(target_date,network)
    ip_poz_dict = ip.create_ip_dict(file_fpath)
    results_file = open("datasets/ip_location_data","w+")
    results_file.write(json.dumps(ip_poz_dict))
    results_file.close()

def add_new_day(target_date): #Date is YYYY-MM-DD format string
    try:
        #Get the first file (.graph will be before .netinfo)
        file_path= get_date_data(target_date,"mainnet")
        print("Got target file:\t"+ file_path)
        date,nodes,chans = db_pop.get_net_data(file_path)

        node_extra_info = [getCapacity(node["pub_key"],chans) for node in nodes]
        nodes_entries, address_entries = createNodeEntries(nodes,date,[ x for [x,y] in node_extra_info ] , [ y for [x,y] in node_extra_info ] )

        edges_entries, policies = createChanEntries(chans,date,nodes_entries)

        print("Created entries for "+ str(len(nodes_entries)) + " nodes and " + str(len(edges_entries)) + " channels " + " date:" + date.strftime("%Y-%m-%d %H:%M:%S") )
    except Exception as e:
        print("ERROR ON DATE: " + target_date + " \t" + str(e))

def data_update(full_date = get_current_date() ):
    if(get_last_logged_date("mainnet") != full_date ):
       print("[Mainnet] Adding day in databaset:\t" + str(full_date))
       add_new_day(full_date)
    else:
       print("[Mainnet] Current day is in databaset")

    if(get_last_logged_date("testnet") != full_date ):
      print("[Testnet] Adding day in databaset:\t" + str(full_date))
      add_new_day(full_date)
    else:
      print("[Testnet] Current day is in databaset")

def dataset_update(metric_list):
    for network in data_location:
        data_set = metrics.process_dataset(data_location[network])
        print("Got metric list:\t"+ str(metric_list))
        for metric in metric_list:
            metrics.generate_and_save(metric,network,data_set)
        print("["+network+"]" + "Updated datasets")

# Last day's data should be in own folder
# Update by putting the last day in
# data_update(get_current_date(timedelta(days=1)))
if __name__ == "__main__":
    print("[Server Upkeep][1/5] Updating IP database")
    ip_map_update(get_last_logged_date("mainnet"),"mainnet")     # Update IP map
    ip_map_update(get_last_logged_date("testnet"),"testnet")
    print("[Server Upkeep][2/5] Updating website database")
    data_update()     #Put new day in db

    #Option for reseting metrics
    if(len(sys.argv) > 1 and sys.argv[1] == "reset"):
        print("[Server Upkeep][Reset] Resetting metrics")
        db_reset_metrics()

    #Check metric presence
    print("[Server Upkeep][3/5] Checking metric presence")
    if(len(Metric.objects.all()) == 0):
        print("[Server Upkeep][3/5] No metrics found, re-creating DB entries")
        db_update_metrics()
    #
    # print("[Server Upkeep][4/5] Updating datasets for metrics")
    # #Update datasets used by metrics
    # dataset_update(get_metric_list())
