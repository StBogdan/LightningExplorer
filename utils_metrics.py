import json
import pickle
import time
import os
import urllib.request
from datetime import datetime
import pickle
import numpy as np

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
    folderList=[x for x in os.listdir(prefix) if os.path.isdir(prefix+ os.sep+ x)]  #Just the folders
    print("Got number of folders:" + str(len(folderList)))
    for folder in folderList :                                                      #Each day
        folderFiles = os.listdir(prefix+ os.sep + folder)
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
                netInfoData = getDataFromFile(prefix+ os.sep + folder + os.sep + statFile)
                # netGraphData= getDataFromFile(prefix+ os.sep + folder + os.sep + statFile.split(".")[0]+ ".graph")

                times.append(summaryTime)
                valuesNrNodes.append(netInfoData["num_nodes"])
                valuesNrEdges.append(netInfoData["num_channels"])
                maxDegs.append(netInfoData["max_out_degree"])
                avgDegs.append(netInfoData["avg_out_degree"])
                valuesNrNodesLonely.append(countNodesNoChan(netGraphData))

                if(inGap):           #Gap checking
                    gaps.append((currentGapStart,summaryTime))
                    inGap= False

                # if(netInfoData["num_channels"] > 3100):     #Anomaly hightlight
                #     print(prefix+ os.sep + folder + os.sep + statFile + "\t\tABNORMAL CHANNEL NUMBER:"+ str(netInfoData["num_channels"]))
                #     # input()

                networkCapacity.append(float(netInfoData["total_network_capacity"])/10**8) #SAT to BTC conversion
                avgChannelSize.append(netInfoData["avg_channel_size"])
            except Exception as e :
                print("On processing\t "+ prefix+ os.sep + folder + os.sep + statFile + " Error:\t"+ str(e))
                if(not inGap):
                    inGap= True
                    currentGapStart = summaryTime
                pass

def plot_NrNodesChans():
        str_dates = [x.strftime("%Y-%m-%d") for x in times]
        return str_dates,[valuesNrNodes,valuesNrEdges]

def plot_NetworkCapacity():
    str_dates = [x.strftime("%Y-%m-%d") for x in times]
    return str_dates,networkCapacity

def plot_AvgChanSize():
    str_dates = [x.strftime("%Y-%m-%d") for x in times]
    return str_dates, avgChannelSize


def plot_avgDegs():
    str_dates = [x.strftime("%Y-%m-%d") for x in times]
    return str_dates, [avgDegs,maxDegs]


def plot_NodesWChannels():
    str_dates = [x.strftime("%Y-%m-%d") for x in times]
    return str_dates,[valuesNrNodes,valuesNrNodesLonely]


def generate_and_save(descriptionString, dataSetPath="/mnt/d/netstates/network_states"):
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

    process_dataset(dataSetPath)
    resultFilePath= "datasets" + os.sep + descriptionString
    results = []
    if(descriptionString == "testnet_avg_chan_size"):
        results= plot_AvgChanSize()
    elif(descriptionString == "testnet_network_capacity" ):
        results = plot_NetworkCapacity()
    elif(descriptionString == "testnet_nr_nodes_chans" ):
        results = plot_NrNodesChans()
    elif(descriptionString == "testnet_avg_degree" ):
        results = plot_avgDegs()
    elif(descriptionString == "testnet_nodes_with_chans" ):
        results = plot_NodesWChannels()
    # elif(descriptionString == "metric_testnet_locations"):
    #     results =plot_NodesWChannels()
    else:
        return "" #Don't write anything to anywhere is no known metric requested


    results_file = open(resultFilePath,"w")
    results_file.write(json.dumps(results))
    results_file.close()
    return resultFilePath #Relative to django project
