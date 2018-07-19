from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse
from nodes.models import *
from datetime import datetime
from utils_site import *


import json
import codecs
import os
import urllib.request

def obtainNetworkData(target_date_logged = Node.objects.all().values("date_logged").last()["date_logged"]):
        # fileName= "newGraph.json"
                # readData = json.loads(codecs.open(fileName, 'r', enc).read())
        # enc='utf-8'
        readData={}
        readData["nodes"] = Node.objects.filter(date_logged= target_date_logged)
        readData["edges"] = Channel.objects.filter(date_logged=target_date_logged)

        return readData

def obtainedCachedPoz():
        fileName= "cachedLocations.json"
        readData = json.loads(open(fileName).read())
        return readData

def obtainNetworkStatistics(): #The output from the output of "lncli getnetworkinfo"
    fileName= open('/etc/django_network_info_path.txt').read().strip()
    enc='utf-8'
    readData = json.loads(codecs.open(fileName, 'r', enc).read())
    date_logged = os.path.getmtime(fileName)
    return [readData,date_logged]

# Create your views here.
def index(request):
    networkStats,date_logged = obtainNetworkStatistics() #Date_logged is unix timestamp as float
    #Convert Sat to BTC
    networkStats["total_network_capacity"] = str(float(networkStats["total_network_capacity"]) / 10**8) +  " BTC"
    networkStats["max_channel_size"] = str(float(networkStats["max_channel_size"]) / 10**8) +" BTC"
    networkStats["avg_channel_size"] = str(networkStats["avg_channel_size"] / 10**8) +" BTC"

    freshness = int( (int(datetime.now().strftime("%s")) - date_logged) /60) #Int nr of mins

    return render(request, 'nodes/index.html', {"networkStats_testnet" : list(networkStats.items()), "last_update" : freshness  })


def about(request):
    return render(request, 'nodes/about.html', {})


def visualiser(request):
    networkData = obtainNetworkData()
    nodePoz = obtainedCachedPoz()

    # networkData =' { "glossary": { "title": "example glossary", "GlossDiv": { "title": "S", "GlossList": { "GlossEntry": { "ID": "SGML", "SortAs": "SGML", "GlossTerm": "Standard Generalized Markup Language", "Acronym": "SGML", "Abbrev": "ISO 8879:1986", "GlossDef": { "para": "A meta-markup language, used to create markup languages such as DocBook.", "GlossSeeAlso": ["GML", "XML"] }, "GlossSee": "markup" } } } } }'
    print(str(len(networkData["nodes"]))+ " with edges " + str(len(networkData["edges"])))

    [networkData,unconnectedNodes] = filterNodes(networkData)
    n,e = prepareGraphData(networkData["nodes"],networkData["edges"])

    # print( [vars(x) for x in networkData["edges"]])
    return render(request, 'nodes/visualiser.html', {"jsonData" : json.dumps({"nodes": n ,"edges": e},default=str)  , "cachedPoz": json.dumps(nodePoz) })

def prepareForPassing(nodeEntries,edgeEntries):
    edgeList = []
    for edge in edgeEntries:
        edgeList.append(db2json_edge(edge))

    nodeList = []
    for nodeEntry in nodeEntries:
        nodeList.append(db2json_node(nodeEntry))
    return nodeList,edgeList

def db2json_node(nodeEntry):
    nodeJSON = vars(nodeEntry)
    nodeJSON.pop("_state")
    nodeJSON.pop("id")
    nodeJSON.pop("date_logged")
    return nodeJSON

def db2json_edge(edgeEntry):
    edgeJSON = vars(edgeEntry)
    edgeJSON["node1_pub"]= edgeEntry.node1_pub.pub_key
    edgeJSON["node2_pub"]= edgeEntry.node2_pub.pub_key
    edgeJSON.pop("_state")
    edgeJSON.pop("id")
    edgeJSON.pop("date_logged")
    return edgeJSON


def prepareGraphData(nodeEntries,edgeEntries):
    edgeList = [{"chan_id": edge.chan_id, "node1_pub":  edge.node1_pub.pub_key , "node2_pub": edge.node2_pub.pub_key, "capacity": edge.capacity  } for edge in edgeEntries]

    nodeList = [{"alias": nodeEntry.alias, "pub_key":  nodeEntry.pub_key , "color": nodeEntry.color, "channels": nodeEntry.channels } for nodeEntry in nodeEntries]
    return nodeList,edgeList


def nodes(request):
        [networkData,unconnectedNodes] = filterNodes(obtainNetworkData())
        paginator_ucn = Paginator([db2json_node(x) for x in unconnectedNodes], 15)

        page= request.GET.get('page')
        uc_nodes = paginator_ucn.get_page(page)
        return render(request, 'nodes/nodes.html', {"unconnectedNodes" : uc_nodes , "connectedNodes" : networkData["nodes"]})

def channels(request):
        graphData = obtainNetworkData()
        all_edges = [db2json_edge(x) for x in graphData["edges"]]
        paginator_edges = Paginator(all_edges, 15)

        page= request.GET.get('page')
        edges = paginator_edges.get_page(page)
        return render(request, 'nodes/channels.html', {"channels" : edges })

def metrics(request):
        if(len(Metric.objects.all()) == 0):
            db_put_metrics(os.listdir("media"),"media")
        metrics = Metric.objects.all()
        for indivMetric in metrics:
            try:
                data_set = json.loads(open(indivMetric.dataset_url).read())
                data_set["data"] = data_set["data"][::80]
                #Scaling to ease load on broswer
                indivMetric.json_data = json.dumps(data_set)
                #TODO Consider scaling factor
            except Exception as e :
                print("Error on dataset load for metric:\t" + indivMetric.title + "\t"+ str(e))
                indivMetric.json_data  = "[]"
        return render(request, 'nodes/metrics.html', {"figures" : metrics})

def nodes_detail(request, nodePubKey,date_logged= Node.objects.all().values("date_logged").first()["date_logged"]):
        if(type(date_logged) is int or date_logged == ""):
            date_logged = datetime.fromtimestamp(int(date_logged))

        networkData = obtainNetworkData(date_logged)
        if(len(networkData["nodes"].filter( pub_key = nodePubKey)) > 1):
            raise Exception("Multiple nodes found for identifier"+ str(pub_key))
        nodeID = networkData["nodes"].filter( pub_key = nodePubKey).first()
        nodeEntries, edgeEntries = getNodeEdges(networkData,nodeID)
        [prepedNodes,prepdEdges] = prepareForPassing(nodeEntries,edgeEntries)

        data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d"), "date_unix": x["date_logged"].strftime("%s")} for x in Node.objects.filter(pub_key= nodePubKey).values("date_logged").distinct().order_by('date_logged')]
        # data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d %H-%M-%S"), "date_unix": x["date_logged"].strftime("%s")} for x in Node.objects.filter(pub_key= nodePubKey).values("date_logged").distinct()]
        return render(request, 'nodes/nodes_detail.html',
                        {"nodes" :json.dumps(prepedNodes),
                        "data_dates": data_dates,
                        "edges" : json.dumps(prepdEdges),
                        "edgeTable": prepdEdges,
                        "nodeInfo" : vars(nodeID),
                        "date_logged": {"date_display": date_logged.strftime("%Y-%m-%d %H:%M"), "date_unix" : date_logged.strftime("%s")}})

def channels_detail(request, chanID,date_logged= Node.objects.all().values("date_logged").first()["date_logged"]):
        if(type(date_logged) is int ):
            date_logged = datetime.fromtimestamp(int(date_logged))
        networkData = obtainNetworkData(date_logged)

        [nodes,edges] = getEdgeConnections(networkData,chanID)
        edgeInfo = networkData["edges"].filter(chan_id=chanID).first()
        data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d"), "date_unix": x["date_logged"].strftime("%s")} for x in Channel.objects.filter(chan_id = chanID).values("date_logged").distinct().order_by('date_logged')]

        # data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d %H-%M-%S"), "date_unix": x["date_logged"].strftime("%s")} for x in Channel.objects.filter(chan_id = chanID).values("date_logged").distinct()]
        n,e = prepareForPassing(nodes,edges)
        print(date_logged.strftime("%Y-%m-%d %H:%M"))
        return render(request, 'nodes/channels_detail.html', {"nodes" : json.dumps(n),
                    "edges" : json.dumps(e),
                    "edgeInfo" : db2json_edge(edgeInfo),
                    "nodesInfo": n ,
                    "data_dates": data_dates,
                    "date_logged": {"date_display": date_logged.strftime("%Y-%m-%d %H:%M"), "date_unix" : date_logged.strftime("%s")}})


def getEdgeConnections(networkGraph, edgeID):
    edgeEntry = networkGraph["edges"].filter(chan_id=edgeID).first()
    if (len(networkGraph["edges"].filter(chan_id=edgeID)) > 1):
        raise Exception("Multiple channels found for identifier"+ str(edgeID))
    assocNodes = [edgeEntry.node1_pub, edgeEntry.node2_pub]

    otherChannelsForNodes=  list(networkGraph["edges"].filter(node1_pub= edgeEntry.node1_pub, node2_pub=edgeEntry.node2_pub).exclude(chan_id=edgeID)) + list(networkGraph["edges"].filter(node1_pub= edgeEntry.node2_pub, node2_pub=edgeEntry.node1_pub).exclude(chan_id=edgeID))


    # vecinNodesIDs = []
    # for edge in networkGraph["edges"]:
    #     if edge["channel_id"] == edgeID:
    #         vecinNodesIDs.append(edge["node1_pub"])
    #         vecinNodesIDs.append(edge["node2_pub"])
    #         break
    # vecinNodesIDs = [edge["node1_pub"] for edge in networkGraph["edges"] if edge["channel_id"] == edgeID ] + [edge["node2_pub"] for edge in networkGraph["edges"] if edge["channel_id"] == edgeID ]
    # edgeNodeDetails = [ node for node in networkGraph["nodes"] if node["pub_key"] in vecinNodesIDs]
    #
    # otherEdges = [edge for edge in networkGraph["edges"] if edge["node2_pub"] in vecinNodesIDs  or  edge["node1_pub"] in vecinNodesIDs]
    return [assocNodes,otherChannelsForNodes+[edgeEntry]]

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
    nodesWithEdges = networkGraph["nodes"].exclude(node1_pub__isnull= True, node2_pub__isnull= True)
    unconnectedNodes = networkGraph["nodes"].filter(node1_pub__isnull= True, node2_pub__isnull= True)
    newNetGraph = {"nodes": nodesWithEdges, "edges": networkGraph["edges"]}

    return [newNetGraph,unconnectedNodes]

    # nodesWithEdges = [edge["node1_pub"] for edge in networkGraph["edges"]] + [edge["node2_pub"] for edge in networkGraph["edges"]]
    # unconnectedNodes=[]
    # i=0
    # while( i< len(networkGraph["nodes"])):
    #     if(not networkGraph["nodes"][i]["pub_key"] in nodesWithEdges):
    #         unconnectedNodes.append(networkGraph["nodes"][i])
    #         networkGraph["nodes"].remove(networkGraph["nodes"][i])
    #     else:
    #         i+=1
    # return [networkGraph,unconnectedNodes]

def getNodeEdges(networkGraph, nodeEntry):

    vecinNodesDuplicates= [nodeEntry] +  [x.node2_pub for x in nodeEntry.node1_pub.all()]+[x.node1_pub for x in nodeEntry.node2_pub.all()]
    vecinNodes = list(set(vecinNodesDuplicates))
    connectedEdges=  list(nodeEntry.node1_pub.all()) + list(nodeEntry.node2_pub.all())

    # vecinNodesIDs = [nodeID] + [edge["node1_pub"] for edge in networkGraph["edges"] if edge["node2_pub"] == nodeID ] + [edge["node2_pub"] for edge in networkGraph["edges"] if edge["node1_pub"] == nodeID]
    #
    # vecinNodesDetails = [ node for node in networkGraph["nodes"] if node["pub_key"] in vecinNodesIDs]
    # connectedEdges = [edge for edge in networkGraph["edges"] if edge["node2_pub"] == nodeID  or  edge["node1_pub"] == nodeID]
    # print("\n\n\n")
    # print( vecinNodes)
    # print("\n\n\n")
    # print( connectedEdges)
    # print("\n\n\n")

    return [vecinNodes,connectedEdges]

def search(request):
    if request.method == 'GET':
        data = obtainNetworkData()
        possibleMatchesNodes=[]
        possibleMatchesEdges=[]
        try:
            raw_search_term =  request.GET['search_term'].strip() #Note that django does automatic html characted sanitising
            if (raw_search_term == ""):
                raise Exception("Empty search query")
            possibleMatchesNodes = list(data["nodes"].filter(pub_key__contains= raw_search_term))
            possibleMatchesNodes +=list(data["nodes"].filter(alias__contains= raw_search_term))
            possibleMatchesEdges = list(data["edges"].filter(chan_id__contains= raw_search_term))
            search_result=  "Found " + str(len(possibleMatchesNodes))+  " matching nodes and " + str(len(possibleMatchesEdges)) + " channels"
            search_term = "Showing results for search term: \"" + raw_search_term + "\""
        except Exception as e:
            print(e)
            search_term = "No search term found"
            search_result = "Please use the navbar to find nodes and edges. You can use their public keys, channel identifiers or aliases to search."

        pmNode,pmEdges = prepareGraphData(possibleMatchesNodes,possibleMatchesEdges)

        return render(request, 'nodes/search.html', {"searchInfo": search_term,  "foundNodes" : pmNode, "foundChannels": pmEdges, "strResults": search_result  })
    else:
        index(request)

    #         status = Nodes.objects.filter(node__icontains=node) # filter returns a list so you might consider skip except part
    #         return render(request,"search.html",{"node":status})
    # else:
    #         return render(request,"search.html",{})
