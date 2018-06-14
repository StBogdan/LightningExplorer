from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse

import json
import codecs
import urllib.request

def obtainNetworkData():
        fileName= "testGraph.json"
        enc='utf-8'
        readData = json.loads(codecs.open(fileName, 'r', enc).read())
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
