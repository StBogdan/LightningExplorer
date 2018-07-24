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
def get_metric_info(file):
    if file == "metric_testnet_avg_chan_size.png":
        return "Average Channel Size", "In Satoshis, how big is your average channel, returned by 'getNetworkInfo'", generate_and_save(file.replace(".png","")),"'scatter'"
    elif file == "metric_testnet_network_capacity.png":
        return "Network capacity", "Total network capacity, in BTC (10^8 or 100 000 000 SAT)", generate_and_save(file.replace(".png","")),"'scatter'"
    elif file == "metric_testnet_nr_nodes_chans.png":
        return "Network presence","Number of nodes with open channels compared to the total number of nodes",generate_and_save(file.replace(".png","")),"'scatter'"
    elif file == "metric_testnet_avg_degree.png":
        return "Average number of channels per node","Showing both the average and the maximum number of channels per node.\nKeep in mind that a significant proportion of nodes do not have open channels", generate_and_save(file.replace(".png","")),"'scatter'"
    elif file == "metric_testnet_nodes_with_chans.png":
        return "Proportion of nodes with channels","The situation is looking more interesting on the mainnet, where the number of channels exceeds the number of nodes, though more data needs to be collected", generate_and_save(file.replace(".png","")),"'scatter'"
    elif file == "metric_testnet_locations.png":
        return "Global distribution of nodes","Based on a location search for the advertised IPs", generate_and_save(file.replace(".png","")),""
    else:
        return "Network statictic","This show a statistic for the network, more information coming soon","",""

data_location = open('/etc/lndmon_data_location.txt').read().strip()
def getDataFromFile(fileName):
    data = json.loads(open(fileName).read())
    # print("Got data " + str(data))
    return data

# TODO Make checks more efficient by not creating anew list of nodes
def countNodesNoChan(networkGraph):

    nodesWithEdges = [edge["node1_pub"] for edge in networkGraph["edges"]] + [edge["node2_pub"] for edge in networkGraph["edges"]]
    unconnectedNodesCount= 0
    for node in networkGraph["nodes"]:
        if not node["pub_key"] in nodesWithEdges:
            unconnectedNodesCount+=1
    return unconnectedNodesCount

def process_dataset(dataSetPath):
    #Array init
    times=[]
    valuesNrNodes=[]
    valuesNrNodesLonely=[]
    valuesNrEdges=[]

    networkCapacity=[]
    avgChannelSize=[]
    gaps=[]
    avgDegs=[]
    maxDegs=[]
    currentGapStart= None

    folderList=[x for x in os.listdir(dataSetPath) if os.path.isdir(dataSetPath+ os.sep+ x)]  #Just the folders
    print("Got number of folders:" + str(len(folderList)))
    for folder in folderList :                                                      #Each day
        folderFiles = os.listdir(dataSetPath+ os.sep + folder)
        netstateFileList = [x for x in folderFiles if x.endswith(".netinfo")]
        print("Folder "+ str(folder) + " has " + str(len(folderFiles)) + "\tout of which " + str(len(netstateFileList)) + " netinfo files")

        inGap = False
        for statFile in netstateFileList:
            try:
                summaryTime= datetime.strptime(statFile.split(".")[0], "%Y-%m-%d-%H:%M:%S")
                print("Metrics: WARNING OLD TIME FORMAT READ")
            except Exception as e:
                summaryTime= datetime.strptime(statFile.split(".")[0], "%Y-%m-%d-%H-%M-%S")
            try:
                netInfoData = getDataFromFile(dataSetPath+ os.sep + folder + os.sep + statFile)
                # netGraphData= getDataFromFile(prefix+ os.sep + folder + os.sep + statFile.split(".")[0]+ ".graph")

                times.append(summaryTime)
                valuesNrNodes.append(netInfoData["num_nodes"])
                valuesNrEdges.append(netInfoData["num_channels"])
                maxDegs.append(netInfoData["max_out_degree"])
                avgDegs.append(netInfoData["avg_out_degree"])
                # valuesNrNodesLonely.append(countNodesNoChan(netInfoData))

                if(inGap):           #Gap checking
                    gaps.append((currentGapStart,summaryTime))
                    inGap= False

                # if(netInfoData["num_channels"] > 3100):     #Anomaly hightlight
                #     print(prefix+ os.sep + folder + os.sep + statFile + "\t\tABNORMAL CHANNEL NUMBER:"+ str(netInfoData["num_channels"]))
                #     # input()

                networkCapacity.append(float(netInfoData["total_network_capacity"])/10**8) #SAT to BTC conversion
                avgChannelSize.append(netInfoData["avg_channel_size"])
            except Exception as e :
                print("On processing\t "+ dataSetPath+ os.sep + folder + os.sep + statFile + " Error:\t"+ str(e))
                print(e)
                if(not inGap):
                    inGap= True
                    currentGapStart = summaryTime
                pass
                # valuesNrNodesLonely
    return times, valuesNrNodes, valuesNrEdges, networkCapacity, avgChannelSize, gaps, avgDegs, maxDegs


def generate_and_save(descriptionString, data_set= ""):
    if(data_set == ""):
        data_set = process_dataset(data_location)
    print("Generating dataset for:\t"+ descriptionString )
    times, valuesNrNodes, valuesNrEdges, networkCapacity, avgChannelSize, gaps, avgDegs, maxDegs = data_set
    str_dates = [x.strftime("%Y-%m-%d %H:%M:%S") for x in times]
    resultFilePath= "datasets" + os.sep + descriptionString
    dataset_template =  {"label": descriptionString, "data": []}
    dataset_template["backgroundColor"]= 'rgba(255, 159, 64, 0.2)'
    dataset_template["borderColor"]=  'rgba(255, 159, 64, 1)'
    results = []

    if(descriptionString == "metric_testnet_avg_chan_size"):
        new_dataset = dataset_template
        new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avgChannelSize)]
        results.append(new_dataset)

    elif(descriptionString == "metric_testnet_network_capacity" ):
        new_dataset = dataset_template.copy()
        new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,networkCapacity)]
        results.append(new_dataset)
    elif(descriptionString == "metric_testnet_nr_nodes_chans" ):
        new_dataset = dataset_template.copy()
        new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,valuesNrNodes)] #,valuesNrNodesLonely]]
        results.append(new_dataset)
    elif(descriptionString == "metric_testnet_avg_degree" ):
        new_dataset = dataset_template.copy()
        new_dataset["label"] = "Average node degree"
        new_dataset["data"]= [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avgDegs)]
        results.append(new_dataset)

        other_dataset = dataset_template.copy()
        other_dataset["label"] = "Maximum node degree"
        other_dataset["backgroundColor"]= 'rgba(153, 102, 255, 0.2)'
        other_dataset["borderColor"]=   'rgba(153, 102, 255, 1)'
        other_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,maxDegs)]
        results.append(other_dataset)
    elif(descriptionString == "metric_testnet_nodes_with_chans" ):
        new_dataset = dataset_template.copy()
        new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,valuesNrNodes)] #,valuesNrNodesLonely]]
        results.append(new_dataset)
    # elif(descriptionString == "metric_testnet_locations"):
    #     results =plot_NodesWChannels()
    else:
        return "" #Don't write anything to anywhere is no known metric requested

    print("Writing results to file:\t" + resultFilePath)
    # (Create and) write result to file
    results_file = open(resultFilePath,"w+")
    results_file.write(json.dumps(results))
    results_file.close()
    return resultFilePath #Relative to django project
