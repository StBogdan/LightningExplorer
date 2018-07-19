import json
import pickle
import time
import os
import urllib.request
from datetime import datetime
import pickle
import numpy as np

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


def generate_and_save(descriptionString, dataSetPath=data_location):
    times, valuesNrNodes, valuesNrEdges, networkCapacity, avgChannelSize, gaps, avgDegs, maxDegs = process_dataset(dataSetPath)
    str_dates = [x.strftime("%Y-%m-%d %H:%M:%S") for x in times]
    resultFilePath= "datasets" + os.sep + descriptionString
    results = {"label": descriptionString, "data": []}

    if(descriptionString == "testnet_avg_chan_size"):
        results["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avgChannelSize)]
    elif(descriptionString == "testnet_network_capacity" ):
        results["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,networkCapacity)]
    elif(descriptionString == "testnet_nr_nodes_chans" ):
        results["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,valuesNrNodes)] #,valuesNrNodesLonely]]
    elif(descriptionString == "testnet_avg_degree" ):
        results["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avgDegs)]

        #TODO ADD me too
        # results["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,maxDegs)]


    elif(descriptionString == "testnet_nodes_with_chans" ):
        results["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,valuesNrNodes)] #,valuesNrNodesLonely]]
    # elif(descriptionString == "metric_testnet_locations"):
    #     results =plot_NodesWChannels()
    else:
        return "" #Don't write anything to anywhere is no known metric requested


    results_file = open(resultFilePath,"w")
    results_file.write(json.dumps(results))
    results_file.close()
    return resultFilePath #Relative to django project
