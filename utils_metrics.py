# Helper and generator for all metrics
# Supposed to help display metrics on website
# Bogdan Stoicescu (bs5017)

import json
import pickle
import time
import os
import urllib.request
from datetime import datetime
import pickle
import numpy as np

#Returns in order,
# title, description, dataset_url, dataset_type, dataset_options,parents (if any)
def get_data_location(network):
    data_location= {"testnet": open('/etc/lndmon_data_location.txt').read().strip() , "mainnet":  open('/etc/lndmon_data_location_mainnet.txt').read().strip()}
    return data_location[network]

def get_metric_info(metric_name,network):
    metric_dict = json.loads(open("metric_dict.json").read())
    if(metric_name in metric_dict ):

        current_metric_dict = metric_dict[metric_name]

        #Fill in some fields with standard values
        if(not "dataset_type" in current_metric_dict):
            current_metric_dict["dataset_type"]= "'line'"

        if(not "dataset_url" in current_metric_dict):
            current_metric_dict["dataset_url"]=  "datasets" + os.sep + network + os.sep + metric_name
        if(not "dataset_labels" in current_metric_dict):
            current_metric_dict["dataset_labels"]=current_metric_dict["dataset_url"]+'_labels'
        if(not "image_url" in current_metric_dict):
            current_metric_dict["image_url"]="media"+ os.sep + network + os.sep + metric_name+".png" #TODO Check prefix requirement
        current_metric_dict["network"]= network
        return metric_dict[metric_name]
    else:
        newMetric = metric_dict["placeholder"]
        newMetric["network"]=network
        return newMetric

data_location = open('/etc/lndmon_data_location.txt').read().strip()

def load_json_file(fileName):
    return json.loads(open(fileName).read())

# TODO Make checks more efficient by not creating anew list of nodes
def count_nodes_nochans(networkGraph):

    nodesWithEdges = [edge["node1_pub"] for edge in networkGraph["edges"]] + [edge["node2_pub"] for edge in networkGraph["edges"]]
    unconnectedNodesCount= 0
    for node in networkGraph["nodes"]:
        if not node["pub_key"] in nodesWithEdges:
            unconnectedNodesCount+=1
    return unconnectedNodesCount

def get_country_node_count():
    ip_data = load_json_file("datasets/ip_location_data")

    country_dict={}
    for ip in ip_data:
        if(ip_data[ip] == "No data" ):
            continue #Pass this ip
        if ip_data[ip]["country"] in country_dict:
            country_dict[ip_data[ip]["country"]]+=1
        else:
            country_dict[ip_data[ip]["country"]]=0
    return country_dict

def count_duplicate_edges(graph_data):
    edges_so_far={}
    duplicates=0
    for chan in graph_data["edges"]:
        if( chan["node1_pub"] in edges_so_far):
            if( chan["node2_pub"] in edges_so_far[chan["node1_pub"]]):
                duplicates+=1
            else:
                edges_so_far[chan["node1_pub"]].append(chan["node2_pub"])
        else:
            edges_so_far[chan["node1_pub"]]=[chan["node2_pub"]]
    return duplicates

def get_average_chan_size(graph_data):
    nr_chans = len(graph_data["edges"])
    chan_size= [int(x["capacity"]) for x in graph_data["edges"]]

    return float(sum(chan_size)/nr_chans)


def process_dataset(dataSetPath):
    #Array init
    times_dict={}
    gaps=[]

    currentGapStart= None

    folder_list=[x for x in os.listdir(dataSetPath) if os.path.isdir(dataSetPath+ os.sep+ x)]  #Just the folders
    print("[DataSet Process] Got number of folders:" + str(len(folder_list)))

    for folder in folder_list :                                                      #Each day
        folderFiles = os.listdir(dataSetPath+ os.sep + folder)
        netstateFileList = [x for x in folderFiles if x.endswith(".netinfo")]       #Each one should have pair ".graph"
        print("[DataSet Process] Folder "+ str(folder) + " has " + str(len(folderFiles)) + "\tof which " + str(len(netstateFileList)) + " netinfo files")

        inGap = False
        for statFile in netstateFileList:
            try:
                summaryTime= datetime.strptime(statFile.split(".")[0], "%Y-%m-%d-%H:%M:%S")
                print("Metrics: WARNING OLD TIME FORMAT READ")
            except Exception as e:
                summaryTime= datetime.strptime(statFile.split(".")[0], "%Y-%m-%d-%H-%M-%S")
            try:
                network_data = load_json_file(dataSetPath+ os.sep + folder + os.sep + statFile)
                graph_data =  load_json_file(dataSetPath+ os.sep + folder + os.sep + statFile.replace(".netinfo",".graph"))

                times_dict[summaryTime]={
                "nodes_nr" : network_data["num_nodes"],
                "chan_nr" : network_data["num_channels"],
                "nodes_nrLonely" : count_nodes_nochans(graph_data),
                "max_degree" : network_data["max_out_degree"],
                "avg_degree" : network_data["avg_out_degree"],
                "capacity_network" : (float(network_data["total_network_capacity"])/10**8), #SAT to BTC conversion
                "duplicate_channels": count_duplicate_edges(graph_data),
                "chan_avg_capacity": get_average_chan_size(graph_data),
                "avg_chan_size" : network_data["avg_channel_size"],
                "min_chan_size" : network_data["min_channel_size"],
                "max_chan_size" : network_data["max_channel_size"]
                }

                if(inGap):           #Gap checking
                    gaps.append((currentGapStart,summaryTime))
                    inGap= False

                # if(network_data["num_channels"] > 3100):     #Anomaly hightlight
                #     print(prefix+ os.sep + folder + os.sep + statFile + "\t\tABNORMAL CHANNEL NUMBER:"+ str(network_data["num_channels"]))
                #     # input()

            except Exception as e :
                error_msg = str(e)
                if(str(e).startswith("Expecting value: line 1 column 1 (char 0)")):
                    error_msg ="Empty file, this is YOUR fault"
                print("[DataSet Process]  On processing\t "+ os.sep + folder + os.sep + statFile + " Error:\t"+ error_msg)
                if(not inGap):
                    inGap= True
                    currentGapStart = summaryTime
                pass
                # nodes_nrLonely
    return times_dict, gaps


def generate_and_save(descriptionString,network, data_set= ""):
    if(data_set == ""):
        data_set = process_dataset(get_data_location(network))
    print("[DataSet Gen] Generating dataset for:\t"+ descriptionString +" network:" + network )
    times_dict, gaps = data_set
    # str_dates = [x.strftime("%Y-%m-%d %H:%M:%S") for x in times]
    resultFilePath= "datasets" + os.sep + network + os.sep + descriptionString

    dataset_template =  {"label": descriptionString, "data": []}
    dataset_template["backgroundColor"]= 'rgba(255, 159, 64, 0.2)'
    dataset_template["borderColor"]=  'rgba(255, 159, 64, 1)'
    results = []

    if(descriptionString == "metric_avg_chan_size"):
        avg_dataset = dataset_template.copy() #Avg chan sizes
        avg_dataset["label"] = "Average channel size"
        avg_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["avg_chan_size"]} for x in sorted(times_dict)]

        min_dataset = dataset_template.copy()   #Min chan sizes
        min_dataset["label"] = "Smallest capacity"
        min_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["min_chan_size"]} for x in sorted(times_dict)]

        max_dataset = dataset_template.copy() #Max chan sizes
        max_dataset["label"] = "Largest capacity"
        max_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["max_chan_size"]} for x in sorted(times_dict)]
        results.append(max_dataset)
        results.append(avg_dataset)
        results.append(min_dataset)

    elif(descriptionString == "metric_network_capacity" ):
        new_dataset = dataset_template.copy()
        # print(list(times_dict))
        # raise Exception("STOP! Checked out these dates")
        new_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["capacity_network"]} for x in sorted(times_dict)]
        # new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,capacity_network)]
        results.append(new_dataset)
    elif(descriptionString == "metric_nr_nodes_chans" ):
        new_dataset = dataset_template.copy()
        new_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["nodes_nr"]} for x in sorted(times_dict)]
        # new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,nodes_nr)] #,nodes_nrLonely]]
        results.append(new_dataset)
    elif(descriptionString == "metric_avg_degree" ):
        new_dataset = dataset_template.copy()
        new_dataset["label"] = "Average node degree"
        new_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["avg_degree"]} for x in sorted(times_dict)]
        # new_dataset["data"]= [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avg_degree)]
        results.append(new_dataset)

        other_dataset = dataset_template.copy()
        other_dataset["label"] = "Maximum node degree"
        other_dataset["backgroundColor"]= 'rgba(153, 102, 255, 0.2)'
        other_dataset["borderColor"]=   'rgba(153, 102, 255, 1)'

        other_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["max_degree"]} for x in sorted(times_dict)]
        # other_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,max_degree)]
        results.append(other_dataset)

    elif(descriptionString == "metric_nodes_with_chans" ):
        new_dataset = dataset_template.copy()
        new_dataset["label"]= "Nodes with channels"
        new_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["nodes_nr"]-times_dict[x]["nodes_nrLonely"]} for x in sorted(times_dict)]
        results.append(new_dataset)

        other_dataset = dataset_template.copy()
        other_dataset["label"] = "Total nodes"
        other_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["nodes_nr"]} for x in sorted(times_dict)]
        results.append(other_dataset)
        # new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,nodes_nr)] #,nodes_nrLonely]]

    elif(descriptionString == "metric_channels" ):
            new_dataset = dataset_template.copy()
            new_dataset["label"]= "Channels"
            new_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["chan_nr"]} for x in sorted(times_dict)]
            results.append(new_dataset)

            other_dataset = dataset_template.copy()
            other_dataset["label"] = "Duplicate channels"
            other_dataset["data"] = [ {"x": x.strftime("%Y-%m-%d %H:%M:%S"), "y": times_dict[x]["duplicate_channels"]} for x in sorted(times_dict)]
            results.append(other_dataset)

    elif(descriptionString == "metric_top_countries" ):
            new_dataset = dataset_template.copy()
            country_dict = get_country_node_count()

            #Get a sorted by value key listdir
            #Reverse it so biggest first
            new_dataset["labels"]= [x for x in sorted(country_dict, key=country_dict.get) if country_dict[x]>0][::-1]
            new_dataset["data"] = [country_dict[x] for x in sorted(country_dict, key=country_dict.get) if country_dict[x]>0 ][::-1] #,nodes_nrLonely]]
            results.append(new_dataset)
    # elif(descriptionString == "metric_locations"):
    #     results =plot_NodesWChannels()
    else:
        print("[DataSet Gen] No generation method for:\t" +descriptionString + " network: " + network)
        return "" #Don't write anything to anywhere is no known metric requested


    # (Create and) write result to file
    for data_set in results:
        if("labels" in data_set ): #Assume one set of labels per metric
            print("[DataSet Gen] Writing labels to file:\t" + resultFilePath+ "_labels")
            labels_file = open(resultFilePath+"_labels","w+")
            labels_file.write(json.dumps(data_set["labels"]))
            labels_file.close()

    print("[DataSet Gen] Writing dataset to file:\t" + resultFilePath)
    results_file = open(resultFilePath,"w+")
    results_file.write(json.dumps(results))
    results_file.close()
    return resultFilePath #Relative to django project
