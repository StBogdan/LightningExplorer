from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse
from nodes.models import Metric

import json
import codecs
import os
import urllib.request

def obtainNetworkData():
        fileName= "newGraph.json"
        enc='utf-8'
        readData = json.loads(codecs.open(fileName, 'r', enc).read())
        # readData={}
        # readData["nodes"] = [var(x) for x in Node.objects.filter(datetime_published__day='21')]
        # readData["edges"] = [var(x) for x in Channel.objects.filter(datetime_published__day='21')]

        return readData

def obtainedCachedPoz():
        fileName= "cachedLocations.json"
        readData = json.loads(open(fileName).read())
        return readData

# Create your views here.
def index(request):
    testJSON = obtainNetworkData()
    nodePoz = obtainedCachedPoz()

    # testJSON =' { "glossary": { "title": "example glossary", "GlossDiv": { "title": "S", "GlossList": { "GlossEntry": { "ID": "SGML", "SortAs": "SGML", "GlossTerm": "Standard Generalized Markup Language", "Acronym": "SGML", "Abbrev": "ISO 8879:1986", "GlossDef": { "para": "A meta-markup language, used to create markup languages such as DocBook.", "GlossSeeAlso": ["GML", "XML"] }, "GlossSee": "markup" } } } } }'
    print(str(len(testJSON["nodes"]))+ " with edges " + str(len(testJSON["edges"])))

    [testJSON,unconnectedNodes] = filterNodes(testJSON)

    return render(request, 'nodes/index.html', {"jsonData" : json.dumps(testJSON) , "unconnectedNodes" : unconnectedNodes , "cachedPoz": json.dumps(nodePoz) })


def nodes(request):
        testJSON = obtainNetworkData()

        # testJSON =' { "glossary": { "title": "example glossary", "GlossDiv": { "title": "S", "GlossList": { "GlossEntry": { "ID": "SGML", "SortAs": "SGML", "GlossTerm": "Standard Generalized Markup Language", "Acronym": "SGML", "Abbrev": "ISO 8879:1986", "GlossDef": { "para": "A meta-markup language, used to create markup languages such as DocBook.", "GlossSeeAlso": ["GML", "XML"] }, "GlossSee": "markup" } } } } }'
        print(str(len(testJSON["nodes"]))+ " with edges " + str(len(testJSON["edges"])))
        [testJSON,unconnectedNodes] = filterNodes(testJSON)
        return render(request, 'nodes/nodes.html', {"unconnectedNodes" : unconnectedNodes })


def nodes_detail(request, nodeID):
        testJSON = obtainNetworkData()
        [nodes,edges] = getNodeEdges(testJSON,nodeID)
        return render(request, 'nodes/nodes_detail.html', {"nodes" : nodes, "edges" : edges, "nodeInfo" : getPubKeyInfo(nodeID)})


def channels(request):
        graphData = obtainNetworkData()
        [nodes,edges] = [graphData["nodes"],graphData["edges"]]

        return render(request, 'nodes/channels.html', {"nodes" : nodes, "channels" : edges })

def metrics(request):
        if(len(Metric.objects.all()) == 0):
            figuresFolder = "media"
            db_put_metrics(os.listdir(figuresFolder),figuresFolder)
        return render(request, 'nodes/metrics.html', {"figures" : Metric.objects.all() })

def db_put_metrics(files,fileURL):
    for file in files:
        # os.getcwd()+os.sep +
        imageSource =  fileURL + os.sep+ file
        newMetric = Metric(image_url = imageSource, title=getTitle(file), description=getDescription(file))
        newMetric.save()
        print("Put metric in database")

def getTitle(file):
    if file == "metric_testnet_avg_chan_size.png":
        return "Average Channel Size"
    elif file == "metric_testnet_network_capacity.png":
        return "Network capacity"
    elif file == "metric_testnet_nr_nodes_chans.png":
        return "Network presence"
    elif file == "metric_testnet_avg_degree.png":
        return "Average number of channels per node"
    elif file == "metric_testnet_nodes_with_chans.png":
        return "Proportion of nodes with channels"
    elif file == "test.png":
        return "Global distribution of nodes"
    else:
        return "Network statictic"

def getDescription(file):
    if file == "metric_testnet_avg_chan_size.png":
        return "In Satoshi, how big is your average channel, returned by 'getNetworkInfo'"
    elif file == "metric_testnet_network_capacity.png":
        return "Total network capacity, in BTC (10^8 or 100 000 000 SAT)"
    elif file == "metric_testnet_nr_nodes_chans.png":
        return "Number of nodes with open channels compared to the total number of nodes"
    elif file == "metric_testnet_avg_degree.png":
        return "Showing both the average and the maximum number of channels per node.\nKeep in mind that a significant proportion of nodes do not have open channels"
    elif file == "metric_testnet_nodes_with_chans.png":
        return "The situation is looking more interesting on the mainnet, where the number of channels exceeds the number of nodes, though more data needs to be collected"
    elif file == "test.png":
        return "Based on a location search for the advertised IPs"
    else:
        return "Network statictic"

def channels_detail(request, chanID):
        testJSON = obtainNetworkData()

        [nodes,edges] = getEdgeConnections(testJSON,chanID)
        edgeInfo = getEdgeDetails(testJSON,chanID)

        return render(request, 'nodes/channels_detail.html', {"nodes" : nodes, "edges" : edges, "edgeInfo" : edgeInfo })

def getEdgeDetails(networkGraph,edgeID):
    for edge in networkGraph["edges"]:
        if edge["channel_id"] == edgeID:
            edgeDetails= edge
            break
    return edgeDetails

def getEdgeConnections(networkGraph, edgeID):
    vecinNodesIDs = []
    for edge in networkGraph["edges"]:
        if edge["channel_id"] == edgeID:
            vecinNodesIDs.append(edge["node1_pub"])
            vecinNodesIDs.append(edge["node2_pub"])
            break
    # vecinNodesIDs = [edge["node1_pub"] for edge in networkGraph["edges"] if edge["channel_id"] == edgeID ] + [edge["node2_pub"] for edge in networkGraph["edges"] if edge["channel_id"] == edgeID ]
    edgeNodeDetails = [ node for node in networkGraph["nodes"] if node["pub_key"] in vecinNodesIDs]

    otherEdges = [edge for edge in networkGraph["edges"] if edge["node2_pub"] in vecinNodesIDs  or  edge["node1_pub"] in vecinNodesIDs]
    return [edgeNodeDetails,otherEdges]

def getPubKeyInfo(pubkey):
    #Get the node alias
    #Uses the 1ml.com API
    url = "https://1ml.com/testnet/node/" + pubkey + "/json"

    with urllib.request.urlopen(url) as openedURL:
        response = openedURL.read()
    dataDict = json.loads(response.decode('utf-8'))
    return dataDict



#TODO Check if pass by refence
#Get the nodes with open channels
def filterNodes(networkGraph):
    nodesWithEdges = [edge["node1_pub"] for edge in networkGraph["edges"]] + [edge["node2_pub"] for edge in networkGraph["edges"]]
    unconnectedNodes=[]
    i=0
    while( i< len(networkGraph["nodes"])):
        if(not networkGraph["nodes"][i]["pub_key"] in nodesWithEdges):
            unconnectedNodes.append(networkGraph["nodes"][i])
            networkGraph["nodes"].remove(networkGraph["nodes"][i])
        else:
            i+=1
    return [networkGraph,unconnectedNodes]

def getNodeEdges(networkGraph, nodeID):
    vecinNodesIDs = [nodeID] + [edge["node1_pub"] for edge in networkGraph["edges"] if edge["node2_pub"] == nodeID ] + [edge["node2_pub"] for edge in networkGraph["edges"] if edge["node1_pub"] == nodeID]

    vecinNodesDetails = [ node for node in networkGraph["nodes"] if node["pub_key"] in vecinNodesIDs]
    connectedEdges = [edge for edge in networkGraph["edges"] if edge["node2_pub"] == nodeID  or  edge["node1_pub"] == nodeID]
    return [vecinNodesDetails,connectedEdges]

def search(request):
    if request.method == 'GET':
        data = obtainNetworkData()
        raw_search_term =  request.GET['search_term'] #Note that django does automatic html characted sanitising
        possibleMatchesNodes = [x for x in data["nodes"] if raw_search_term in x["pub_key"]] +  [x for x in data["nodes"] if raw_search_term in x["alias"]]

        possibleMatchesEdges =  [x for x in data["edges"] if (raw_search_term in x["channel_id"]) or (raw_search_term in x["chan_point"]) ]

        return render(request, 'nodes/search.html', {"searchInfo": raw_search_term,  "foundNodes" : possibleMatchesNodes, "foundChannels": possibleMatchesEdges, "nrResults": len(possibleMatchesNodes)+ len(possibleMatchesEdges)})
    else:
        index(request)

    #         status = Nodes.objects.filter(node__icontains=node) # filter returns a list so you might consider skip except part
    #         return render(request,"search.html",{"node":status})
    # else:
    #         return render(request,"search.html",{})
