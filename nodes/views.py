from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse
from nodes.models import *
from datetime import datetime
from utils_db_upkeep import *
from django.shortcuts import redirect
import thunder as thunder

import json
import codecs
import os
import urllib.request

from utils_config import *

def generate_chart_dataset(descriptionString, target, logged_time):
    print("Generating dataset for:\t"+ descriptionString +"\t for time\t"+ logged_time.strftime("%Y-%m-%d %H:%M:%S")  )

    dataset_template =  {"label": descriptionString, "data": []}
    dataset_template["backgroundColor"]= 'rgba(255, 159, 64, 0.2)'
    dataset_template["borderColor"]=  'rgba(255, 159, 64, 1)'
    results = []


    if(descriptionString == "node_capacity"):
        new_dataset = dataset_template
        options= "options: { scales: { xAxes: [{ type: 'time' }] }}"
        labels=""

        data_query_result= Node.objects.filter(pub_key=target).order_by("date_logged")
        new_dataset["data"] = [ {"x": x.date_logged.strftime("%Y-%m-%d %H:%M:%S:%f"), "y": x.capacity} for x in data_query_result ]
        # new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avg_chan_size)]
        results.append(new_dataset)
    elif(descriptionString == "node_channels"):
        new_dataset = dataset_template
        options= "options: { scales: { xAxes: [{ type: 'time' }] }}"
        labels=""

        data_query_result= Node.objects.filter(pub_key=target).order_by("date_logged")
        new_dataset["data"] = [ {"x": x.date_logged.strftime("%Y-%m-%d %H:%M:%S"), "y": x.channels} for x in data_query_result ]
        # new_dataset["data"] = [ {"x": time, "y":data_point } for time,data_point in zip(str_dates,avg_chan_size)]
        results.append(new_dataset)

    return results,options,labels


def get_last_logged_date(network_on):
     return Node.objects.filter(network= network_on).values("date_logged").last()["date_logged"]

def get_network_data(target_date_logged = "", network="testnet"):
        if(target_date_logged == ""):
            target_date_logged = get_last_logged_date(network)
        # fileName= "newGraph.json"
                # readData = json.loads(codecs.open(fileName, 'r', enc).read())
        # enc='utf-8'
        readData={}
        readData["nodes"] = Node.objects.filter(date_logged= target_date_logged)
        readData["edges"] = Channel.objects.filter(date_logged=target_date_logged)

        return readData

def get_graph_cache(network="testnet"):
        fileName= "cachedLocations-"+ network+".json"
        readData = json.loads(open(fileName).read())
        return readData

def obtainNetworkStatistics(target_config_file): #The output from the output of "lncli getnetworkinfo"
    enc='utf-8'
    readData = json.loads(codecs.open(target_config_file, 'r', enc).read())
    date_logged = os.path.getmtime(target_config_file)
    return [readData,date_logged]

# Create your views here.
def index(request):
    netstats={"mainnet": [], "testnet":[]}
    try:    #First set of statistics LOCAL NODE NETWORK
        networkStats,date_logged = obtainNetworkStatistics(site_config["network_info_path"]) #Date_logged is unix timestamp as float
        #Convert Sat to BTC
        networkStats["total_network_capacity"] = str(float(networkStats["total_network_capacity"]) / 10**8) +  " BTC"
        networkStats["max_channel_size"] = str(float(networkStats["max_channel_size"]) / 10**8) +" BTC"
        networkStats["avg_channel_size"] = str(networkStats["avg_channel_size"] / 10**8) +" BTC"

        freshness = int( (int(datetime.now().strftime("%s")) - date_logged) /60) #Int nr of mins
        netstats[site_config["node_network"]] = [networkStats, freshness]
    except Exception as e:
        print("Error on " + site_config["node_network"] + " stat fetch:\t"+ str(e))
        netstats[site_config["node_network"]] = [{}, "Some time ago"]

    othernet = "mainnet" if site_config["node_network"]=="testnet" else "testnet"
    try:
        networkStats,date_logged = obtainNetworkStatistics(site_config["network_info_"+othernet]) #Date_logged is unix timestamp as float
        #Convert Sat to BTC
        networkStats["total_network_capacity"] = str(float(networkStats["total_network_capacity"]) / 10**8) +  " BTC"
        networkStats["max_channel_size"] = str(float(networkStats["max_channel_size"]) / 10**8) +" BTC"
        networkStats["avg_channel_size"] = str(networkStats["avg_channel_size"] / 10**8) +" BTC"

        freshness = int( (int(datetime.now().strftime("%s")) - date_logged) /60) #Int nr of mins
        netstats[othernet] = [networkStats, freshness]
    except Exception as e:
        print("Error on+ " + othernet + " stat fetch:\t"+ str(e))
        netstats[othernet] = [{}, "Some time ago"]

    return render(request, 'nodes/index.html', {"networkStats_testnet" : list(netstats["testnet"][0].items()), "networkStats_mainnet": list(netstats["mainnet"][0].items()),"last_update_testnet" : netstats["testnet"][1] , "last_update_mainnet" : netstats["mainnet"][1]  })


def about(request):
    return render(request, 'nodes/about.html', {})




def visualiser(request,network,date_logged= ""):
    if(date_logged== ""):
        return redirect("/" + network+'/visualiser/'+ get_last_logged_date(network).strftime("%s"))
    if(type(date_logged) is int or date_logged == ""):
        date_logged = datetime.fromtimestamp(int(date_logged))



    networkData = get_network_data(date_logged,network)
    nodePoz = get_graph_cache(network)

    # networkData =' { "glossary": { "title": "example glossary", "GlossDiv": { "title": "S", "GlossList": { "GlossEntry": { "ID": "SGML", "SortAs": "SGML", "GlossTerm": "Standard Generalized Markup Language", "Acronym": "SGML", "Abbrev": "ISO 8879:1986", "GlossDef": { "para": "A meta-markup language, used to create markup languages such as DocBook.", "GlossSeeAlso": ["GML", "XML"] }, "GlossSee": "markup" } } } } }'
    print("Got cache and node and edge data "+ str(len(networkData["nodes"]))+ " with edges " + str(len(networkData["edges"])) )

    [networkData,unconnectedNodes] = filterNodes(networkData)
    n,e = prepareGraphData(networkData["nodes"],networkData["edges"])
    # n,e = list(networkData["nodes"]),list(networkData["edges"])

    print("Data filtered and prepared ")
    # print( [vars(x) for x in networkData["edges"]])
    return render(request, 'nodes/visualiser.html', {"jsonData" : json.dumps({"nodes": n ,"edges": e},default=str)  , "cachedPoz": json.dumps(nodePoz), "network": network , "date_logged": date_logged, "chan_count" : len(e), "nodes_count": len(n)})

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
    nodeJSON["addresses"]=[db2json_adr(adr) for adr in nodeEntry.address_set.all()]
    nodeJSON.pop("_state")
    nodeJSON.pop("id")
    nodeJSON.pop("date_logged")
    return nodeJSON

def db2json_adr(addressEntry):
    adrJSON = vars(addressEntry)
    adrJSON.pop('id')
    adrJSON.pop('node_id')
    adrJSON.pop("_state")
    adrJSON.pop('date_logged')
    print(adrJSON)
    return adrJSON


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


def nodes(request,network, date_logged=""):
        if(date_logged== ""):
            return redirect("/" + network+'/nodes/' + get_last_logged_date(network).strftime("%s"))
        if(type(date_logged) is int or date_logged == ""):
            date_logged_unix=date_logged
            date_logged = datetime.fromtimestamp(int(date_logged))

        [networkData,unconnectedNodes] = filterNodes(get_network_data(date_logged,network))
        paginator_ucn = Paginator(networkData["nodes"], 15)
        print(len(networkData["nodes"]))

        page= request.GET.get('page')
        nodes_page = paginator_ucn.get_page(page)
        print(nodes_page)
        nodes_page.object_list = [db2json_node(x) for x in nodes_page.object_list]

        return render(request, 'nodes/nodes.html', {"nodes" : nodes_page, "network":network, "date_logged": date_logged, "date_logged_unix": date_logged_unix})

def channels(request,network, date_logged=""):
        if(date_logged== ""):
            return redirect("/" + network+'/channels/' + get_last_logged_date(network).strftime("%s"))
        if(type(date_logged) is int or date_logged == ""):
            date_logged_unix= date_logged
            date_logged = datetime.fromtimestamp(int(date_logged))


        graphData = get_network_data(date_logged,network)
        # print(graphData)
        paginator_edges = Paginator(graphData["edges"], 15)

        page= request.GET.get('page')
        channels_page = paginator_edges.get_page(page)
        channels_page.object_list = [db2json_edge(x) for x in channels_page.object_list]

        return render(request, 'nodes/channels.html', {"channels" : channels_page , "network":network, "date_logged" : date_logged, "date_logged_unix": date_logged_unix})

def metrics(request,network):
        filter_sieve=1

        metrics = Metric.objects.filter(network=network)
        for single_metric in metrics:
            try:
                data_sets = json.loads(open(single_metric.dataset_url).read())
                #Scaling (get every 80th datapoint) to ease load on broswer
                #TODO Consider scaling factor
                try:
                    data_labels = json.loads(open(single_metric.dataset_labels).read())
                    filter_sieve=4 #if has labels, less sieving for preview
                    data_labels= data_labels[0:int(len(data_labels)/filter_sieve)]
                    single_metric.labels = json.dumps(data_labels) #Empty file SHOULD raise an exception here
                except Exception as e:
                    print("Error on labels load for metric:\t" + single_metric.title + "\t"+ str(e))

                for one_set in data_sets:
                    if(hasattr(single_metric,"labels")):
                        one_set["data"] = one_set["data"][0:int(len(one_set["data"])/filter_sieve)]
                    else:
                        one_set["data"] = one_set["data"][::filter_sieve]

                single_metric.json_data = json.dumps(data_sets)
            except Exception as e :
                print("Error on dataset load for metric:\t" + single_metric.title + "\t"+ str(e))
                single_metric.dataset_url="" #Trigger image backup
                single_metric.json_data  = ""

        return render(request, 'nodes/metrics.html', {"figures" : metrics, "network": network})

def metric_detail(request, metricID,network):
        try:    #DB fetch
            single_metricQuery = Metric.objects.filter(id= int(metricID))
            if( len(single_metricQuery) != 1):
                raise Http404("Unable to find metric by given ID")
            single_metric=single_metricQuery[0]
            filter_sieve= 1
        except Exception as e:
            print("Error on database load for metric ID:\t" + metricID + "\t"+ str(e))
            raise Http404("Unable to find metric by given ID")

        try:     #Dataset fetch
            data_sets = json.loads(open(single_metric.dataset_url).read())
            try:
                data_labels = json.loads(open(single_metric.dataset_labels).read())
                single_metric.labels = json.dumps(data_labels)
                filter_sieve=1 #if has labels, no sieving
            except Exception as e:
                print("Error on labels load for metric ID:\t" + metricID + "\t"+ str(e))
            #Scaling (get every 80th datapoint) to ease load on broswer
            #TODO Consider scaling factor
            for one_set in data_sets:
                one_set["data"] = one_set["data"][::filter_sieve]

            single_metric.json_data = json.dumps(data_sets)

        except Exception as e :
            print("Error on dataset load for metric ID:\t" + single_metric.title + "\t"+ str(e))
            single_metric.dataset_url="" #Trigger image backup
            single_metric.json_data  = "[]"

        print(single_metric.dataset_type)
        return render(request, 'nodes/metric_detail.html', {"metric" : single_metric, "network": network})


def nodes_detail(request, nodePubKey, network, date_logged= ""):
        if(date_logged== ""):
            return redirect("/" + network+'/node/' + nodePubKey + "/"+ get_last_logged_date(network).strftime("%s"))
        if(type(date_logged) is int or date_logged == ""):
            date_logged = datetime.fromtimestamp(int(date_logged))

        networkData = get_network_data(date_logged,network)
        if(len(networkData["nodes"].filter( pub_key = nodePubKey)) > 1):
            raise Exception("Multiple nodes found for identifier"+ str(pub_key))
        nodeID = networkData["nodes"].filter( pub_key = nodePubKey).first()
        nodeEntries, edgeEntries = getNodeEdges(networkData,nodeID)
        [prepedNodes,prepdEdges] = prepareForPassing(nodeEntries,edgeEntries)


        js_dataset_capacity,js_options,js_labels_capacity =generate_chart_dataset("node_capacity",nodePubKey,date_logged)
        js_dataset_chans,js_options,js_labels_chans =generate_chart_dataset("node_channels",nodePubKey,date_logged)

        data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d %H:%M:%S"), "date_unix": x["date_logged"].strftime("%s")} for x in Node.objects.filter(pub_key= nodePubKey).values("date_logged").distinct().order_by('date_logged')]
        # data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d %H-%M-%S"), "date_unix": x["date_logged"].strftime("%s")} for x in Node.objects.filter(pub_key= nodePubKey).values("date_logged").distinct()]

        print("-----------------------")
        print(js_dataset_capacity[0]["data"][0])
        print("-----------------------")
        print(js_dataset_chans[0]["data"][0])
        print("-----------------------")
        print(data_dates[0])
        print("-----------------------")
        return render(request, 'nodes/nodes_detail.html',
                        {"nodes" :json.dumps(prepedNodes),
                        "data_dates": data_dates,
                        "edges" : json.dumps(prepdEdges),
                        "edgeTable": prepdEdges,
                        "nodeInfo" : vars(nodeID),
                        "chart_dataset_capacity": json.dumps(js_dataset_capacity),
                        "chart_dataset_chans": json.dumps(js_dataset_chans),
                        "chart_options": js_options,
                        "chart_labels_capacity": json.dumps(js_labels_capacity),
                        "chart_labels_chans": json.dumps(js_labels_chans),
                        "date_logged": {"date_display": date_logged.strftime("%Y-%m-%d %H:%M"), "date_unix" : date_logged.strftime("%s")},
                        "network" : network})



def channel_detail(request, chanID,date_logged= "",network = "testnet"):
        if(date_logged==""):
            return redirect("/" + network+'/channel/' + chanID + "/"+ get_last_logged_date(network).strftime("%s"))
        if(type(date_logged) is int ):
            date_logged = datetime.fromtimestamp(int(date_logged))
        networkData = get_network_data(date_logged,network)

        [nodes,edges] = getEdgeConnections(networkData,chanID)
        edgeInfo = networkData["edges"].filter(chan_id=chanID).first()
        data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d"), "date_unix": x["date_logged"].strftime("%s")} for x in Channel.objects.filter(chan_id = chanID).values("date_logged").distinct().order_by('date_logged')]

        # data_dates = [{"date_display": x["date_logged"].strftime("%Y-%m-%d %H-%M-%S"), "date_unix": x["date_logged"].strftime("%s")} for x in Channel.objects.filter(chan_id = chanID).values("date_logged").distinct()]
        n,e = prepareForPassing(nodes,edges)
        print([x for x in n])
        print(date_logged.strftime("%Y-%m-%d %H:%M"))
        return render(request, 'nodes/channels_detail.html', {"nodes" : json.dumps(n),
                    "edges" : json.dumps(e),
                    "edgeInfo" : db2json_edge(edgeInfo),
                    "nodesInfo": n ,
                    "data_dates": data_dates,
                    "date_logged": {"date_display": date_logged.strftime("%Y-%m-%d %H:%M"), "date_unix" : date_logged.strftime("%s")},
                    "network": network})


def getEdgeConnections(networkGraph, edgeID):
    print(networkGraph["edges"].filter(chan_id=edgeID))
    print(edgeID)
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
    # unconnectedNodes = networkGraph["nodes"].filter(node1_pub__isnull= True, node2_pub__isnull= True)
    return [{"nodes": nodesWithEdges, "edges": networkGraph["edges"]},{}]

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

def search(request,network):
    on_network = network #Avoid naming confusion on databae lookup
    if request.method == 'GET':
        data = get_network_data(get_last_logged_date(network),network)
        possibleMatchesNodes=[]
        possibleMatchesEdges=[]
        try:
            raw_search_term =  request.GET['search_term'].strip() #Note that django does automatic html characted sanitising
            if (raw_search_term == ""):
                raise Exception("Empty search query")
            possibleMatchesNodes = list(data["nodes"].filter(network= on_network, pub_key__contains= raw_search_term))
            possibleMatchesNodes +=list(data["nodes"].filter(network= on_network,alias__contains= raw_search_term))
            possibleMatchesEdges = list(data["edges"].filter(network= on_network,chan_id__contains= raw_search_term))
            search_result=  "Found " + str(len(possibleMatchesNodes))+  " matching nodes and " + str(len(possibleMatchesEdges)) + " channels"
            search_term = "Showing results for search term: \"" + raw_search_term + "\" on the Bitcoin "+ network + "."
        except Exception as e:
            print(e)
            search_term = "No search term found"
            search_result = "Please use the navbar to find nodes and edges. You can use their public keys, channel identifiers or aliases to search. Alternatively try, the other network."

        pmNode,pmEdges = prepareGraphData(possibleMatchesNodes,possibleMatchesEdges)

        return render(request, 'nodes/search.html', {"searchInfo": search_term,  "foundNodes" : pmNode, "foundChannels": pmEdges, "strResults": search_result, "network": on_network  })
    else:
        index(request)

    #         status = Nodes.objects.filter(node__icontains=node) # filter returns a list so you might consider skip except part
    #         return render(request,"search.html",{"node":status})
    # else:
    #         return render(request,"search.html",{})


def get_node_details_api(node_dict):
    result={}
    result["info_given"]=node_dict
    try:
        stub,macaroon = thunder.startServerConnection(node_dict)
        result["info"]    = thunder.get_info_dict(stub,macaroon)
        result["channels"]= thunder.getCurrentChannels(stub,macaroon)
        result["peers"]   = (thunder.getPeers(stub,macaroon)).peers
        result["fees"]  = thunder.getFeeReport(stub,macaroon)
        # print(result["fees"])
    except Exception as e :
        print("Data not available, error:\t"+str(e))
        result["info"] = "Data not available, error:\t"+str(e)
    return result



def active_dashboard(request):
    # username = request.POST['username']
    # password = request.POST['password']
    # user = authenticate(request, username=username, password=password)
    # if user is not None:
    #     login(request, user)
        # Redirect to a success page.
    own_nodes = thunder.getServerConfigs()
    node_results=[]
    for node in own_nodes:
        node_results.append(get_node_details_api(node))

    return render(request, 'nodes/active.html', {"node_detail_list": node_results})
    # else:
    #     # Return an 'invalid login' error message.
    #     return Http404()



def active_node_detail(request,node_pubkey):
    own_nodes = thunder.getServerConfigs()
    target_node = [x for x in own_nodes if x["pubkey"] == node_pubkey][0] #Should only be one
    node_detail =  get_node_details_api(target_node)
    return render(request, 'nodes/active_detail.html', {"node": node_detail})

def active_channel_detail(request,node_pubkey,chan_id):
    return render(request, 'nodes/active.html', {})


from django.contrib.auth import authenticate, login
