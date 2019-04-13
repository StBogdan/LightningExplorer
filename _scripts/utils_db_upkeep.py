import os
import json
from datetime import datetime
from datetime import timedelta
from _scripts import utils_metrics as metrics, utils_IP as Ip, utils_databasePopulate as Db_pop, utils_config as config
import sys
from nodes.models import *

"""
What: Script for adding new dates into the Postgres database 
        For website visualisation
Why: Automate database population
"""

# Setup django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
# django.setup()
# from nodes.models import *

site_config = config.get_site_config()
data_location = {"testnet": site_config["lndmon_data_location"],
                 "mainnet": site_config["lndmon_data_location_mainnet"]}


def db_put_metrics(metric_list):
    for metric_name in metric_list:
        print(f"Putting metric in database:\t{metric_name}")

        metric_dict = metrics.get_metric_info(metric_name, "mainnet")
        main_metric = Metric(
            title=metric_dict["title"],
            description=metric_dict["description"],
            dataset_type=metric_dict["dataset_type"],
            dataset_options=metric_dict["dataset_options"],
            dataset_url=metric_dict["dataset_url"],
            dataset_labels=metric_dict["dataset_labels"],
            image_url=metric_dict["image_url"],
            network=metric_dict["network"])

        metric_dict_testnet = metrics.get_metric_info(metric_name, "testnet")
        test_metric = Metric(
            title=metric_dict_testnet["title"],
            description=metric_dict_testnet["description"],
            dataset_type=metric_dict_testnet["dataset_type"],
            dataset_options=metric_dict_testnet["dataset_options"],
            dataset_url=metric_dict_testnet["dataset_url"],
            dataset_labels=metric_dict_testnet["dataset_labels"],
            image_url=metric_dict_testnet["image_url"],
            network=metric_dict_testnet["network"])

        main_metric.save()
        test_metric.save()


def db_update_metrics():
    """Create db entries for metric, both mainnet and testnet"""
    db_put_metrics(get_metric_list())


def db_reset_metrics():
    print("Removing all metrics currently in database")
    Metric.objects.all().delete()


def get_last_logged_date(on_network):
    try:
        last_date = Node.objects.filter(network=on_network).values("date_logged").first()["date_logged"].strftime(
            "%Y-%m-%d")
    except Exception as e:
        print("[Server Upkeep] Failed to get last date:\t" + str(e))
        last_date = "No dates logged"
    return last_date


def get_current_date(time_offset=timedelta()):
    return (datetime.now() - time_offset).strftime("%Y-%m-%d")


def get_metric_list():
    # look in the db, grab all metrics and get their name (cut off the "media/" prefix)
    return [x for x in json.loads(open("metric_dict.json").read())]


def get_date_data(target_date, network):
    print(get_last_logged_date(network))
    print("[DB Upkeep] Get date data in:\t" + data_location[network] + os.sep + target_date)
    datafiles = os.listdir(data_location[network] + os.sep + target_date)
    first_file = [x for x in datafiles if x.endswith(".graph")][0]
    file_path = data_location[network] + os.sep + target_date + os.sep + first_file
    return file_path


def ip_map_update(target_date, network):
    file_fpath = get_date_data(target_date, network)
    ip_poz_dict = Ip.create_ip_dict(file_fpath)
    results_file = open("datasets" + os.sep + network + os.sep + "ip_location_data", "w+")
    results_file.write(json.dumps(ip_poz_dict))
    results_file.close()


def add_new_day(target_date):  # Date is YYYY-MM-DD format string
    try:
        # Get the first file (.graph will be before .netinfo)
        file_path = get_date_data(target_date, "mainnet")
        print("Got target file:\t" + file_path)
        date, nodes, chans = Db_pop.get_net_data(file_path)

        node_extra_info = [Db_pop.get_node_capacity(node["pub_key"], chans) for node in nodes]
        nodes_entries, address_entries = Db_pop.createNodeEntries(nodes, date, [x for [x, y] in node_extra_info],
                                                                  [y for [x, y] in node_extra_info])

        edges_entries, policies = Db_pop.createChanEntries(chans, date, nodes_entries)

        print("Created entries for " + str(len(nodes_entries)) + " nodes and " + str(
            len(edges_entries)) + " channels " + " date:" + date.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        print("ERROR ON DATE: " + target_date + " \t" + str(e))


def add_latest_data(directory_fpath="", network="testnet", hourly=False):
    current_day = -1
    current_hour = -1
    for file in sorted(os.listdir(directory_fpath)):
        try:
            if not file.endswith(".graph"):
                continue

            summary_time = datetime.strptime(file.split(".")[0], "%Y-%m-%d-%H-%M-%S")
            if current_hour != summary_time.hour or current_day != summary_time.day:
                print("[Data Update][" + network + "][Hourly process] Process Hour: " + str(
                    summary_time.hour) + " Day: " + str(summary_time.day) + " previous\t Hour:" + str(
                    current_hour) + " on Day:" + str(current_day))
                current_hour = summary_time.hour
                current_day = summary_time.day
            else:
                print(f"[Data Update][{network}][Hourly process] Continue Hour: {summary_time.hour} "
                      f"on Day: {summary_time.day} compare to last seen {current_hour} on {current_day}")
                continue
            if len(Node.objects.filter(date_logged=summary_time)) > 0:
                print("[Data Update][" + network + "] Date already in database\t" + str(summary_time))
                continue

            file_path = directory_fpath + os.sep + file
            print("Got target file:\t" + file_path)
            date, nodes, chans = Db_pop.get_net_data(file_path)
            node_extra_info = [Db_pop.get_node_capacity(node["pub_key"], chans) for node in nodes]
            nodes_entries, address_entries = Db_pop.createNodeEntries(nodes, date, [x for [x, y] in node_extra_info],
                                                                      [y for [x, y] in node_extra_info], network)
            edges_entries, policies = Db_pop.createChanEntries(chans, date, nodes_entries, network)
            print(
                "[Data Update][" + network + "][ Created entries for " + str(len(nodes_entries)) + " nodes and " + str(
                    len(edges_entries)) + " channels " + " date:" + date.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            print("[Data Update][" + network + "] ERROR:" + str(e))


def data_update(full_date=get_current_date()):
    if get_last_logged_date("mainnet") != full_date:
        print("[Mainnet] Adding day in databaset:\t" + str(full_date))
        add_new_day(full_date)
    else:
        print("[Mainnet] Current day is in databaset")

    if get_last_logged_date("testnet") != full_date:
        print("[Testnet] Adding day in databaset:\t" + str(full_date))
        add_new_day(full_date)
    else:
        print("[Testnet] Current day is in databaset")


def dataset_update(metric_list):
    for network in data_location:
        data_set = metrics.process_dataset(data_location[network], True)
        print("Got metric list:\t" + str(metric_list))
        for metric in metric_list:
            metrics.generate_and_save(metric, network, data_set)
        print("[" + network + "]" + "Updated datasets")


# Last day's data should be in own folder
# Update by putting the last day in
# data_update(get_current_date(timedelta(days=1)))
if __name__ == "__main__":
    print("[Server Upkeep][1/5] Updating IP database")
    ip_map_update(get_last_logged_date("mainnet"), "mainnet")  # Update IP map
    ip_map_update(get_last_logged_date("testnet"), "testnet")
    print("[Server Upkeep][2/5] Updating website database")
    data_update()  # Put new day in db

    # Option for reseting metrics
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        print("[Server Upkeep][Reset] Resetting metrics")
        db_reset_metrics()

    if len(sys.argv) > 1 and sys.argv[1] == "update_current_day":
        print("[Server Upkeep][Force-update] Adding current day info")
        add_latest_data()

    if len(sys.argv) > 1 and sys.argv[1] == "hourly":
        print("[Server Upkeep][Force-update] Adding current day info for network: ")
        add_latest_data(site_config["logging_dir"], site_config["node_network"], True)

    # Check metric presence
    print("[Server Upkeep][3/5] Checking metric presence")
    if len(Metric.objects.all()) == 0:
        print("[Server Upkeep][3/5] No metrics found, re-creating DB entries")
        db_update_metrics()

    print("[Server Upkeep][4/5] Updating datasets for metrics")
    dataset_update(get_metric_list())
