import os,django
import json
from datetime import datetime


#Django setup (run in the virtual environemt)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
django.setup()
data_location = open('/etc/lndmon_data_location.txt').read().strip()
from nodes.models import *

def getFiles(full_data_path, one_per_day = 0):
    files= []
    for day_dir in os.listdir(full_data_path):
        # print("In folder " + full_data_path+ os.sep + day_dir )
        if(not os.path.isdir(full_data_path+ os.sep + day_dir)):
            continue

        if one_per_day:
            day_data = os.listdir(full_data_path+ os.sep + day_dir)[0:2] #Should get a .graph and .netinfo file in there
        else:
            day_data = os.listdir(full_data_path+ os.sep + day_dir)
        files+= [full_data_path+ os.sep + day_dir + os.sep + x for x in day_data if x.endswith(".graph")]
    return files


def getCapacity(nodeID,channelArray):
    capacity=0
    channels=0
    for edge in channelArray:
        if( edge["node1_pub"] == nodeID or edge["node2_pub"] == nodeID):
            capacity+= int(edge["capacity"])
            channels+=1
    return [channels,capacity]


def getNetworkData(filePath):
    fileName= filePath.split(os.sep)[-1]
    try:
        date= datetime.strptime(fileName.split(".")[0], "%Y-%m-%d-%H-%M-%S")
    except Exception as e:
        date= datetime.strptime(fileName.split(".")[0], "%Y-%m-%d-%H:%M:%S")
    netData = json.loads(open(filePath).read())
    return [date,netData["nodes"],netData["edges"]]

def createNodeEntries(nodes_info,node_date,nodes_chans,nodes_capacity):
    new_nodes= []
    new_nodes_dict={}
    new_addresses = []
    index =0
    for node_info in nodes_info:
        nodeObj = Node(date_logged = node_date,
                                        last_update = node_info["last_update"],
                                        pub_key = node_info["pub_key"],
                                        alias = node_info["alias"],
                                        color = node_info["color"],
                                        channels = nodes_chans[index],
                                        capacity = nodes_capacity[index])
        new_nodes.append(nodeObj)
        new_nodes_dict[node_info["pub_key"]]= nodeObj;
        index+=1

    #Saves the enties, making nodes_dict usable for edge creation
    new_node_entries = Node.objects.bulk_create(new_nodes)
    index =0
    for node_info in nodes_info:
        if( new_node_entries[index].pub_key != node_info["pub_key"]):
            raise Exception("Node identity mismatch")

        for adAdr in node_info["addresses"]:
            new_addresses.append(Address(date_logged = node_date,
                                        node       = new_node_entries[index],
                                        addr       = adAdr["addr"],
                                        network    = adAdr["network"]))
        index+=1

    new_addresses_entries = Address.objects.bulk_create(new_addresses)
    return new_nodes_dict, new_addresses



def createChanEntries(edges_info,edge_date,nodes_entries):
    # print(edge_info)
    # print("Got friends" + str(nodes_entries[edge_info["node1_pub"]][0]) + " ------AND-----"  + str(nodes_entries[edge_info["node2_pub"]][0]))
    new_chans = []
    new_entries_policies=[]

    for edge_info in edges_info:
        new_chans.append( Channel(date_logged= edge_date,
                 chan_id     = edge_info["channel_id"],
                 last_update = edge_info["last_update"],
                 node1_pub   = nodes_entries[edge_info["node1_pub"]], #As first elem is node, others are the addresses
                 node2_pub   = nodes_entries[edge_info["node2_pub"]],
                 capacity    = edge_info["capacity"],
                 chan_point   =edge_info["chan_point"]))

    new_chan_entries = Channel.objects.bulk_create(new_chans)
    index =0
    for edge_info in edges_info:
        if(new_chans[index].chan_id !=  edge_info["channel_id"]):
            raise Exception("Channel identity mismatch")

        if(edge_info["node1_policy"] != None):
            new_entries_policies.append(Node_Policy(date_logged = edge_date,
                    channel =new_chans[index],
                    node =  nodes_entries[edge_info["node1_pub"]],
                    time_lock_delta     = edge_info["node1_policy"]["time_lock_delta"],
                    min_htlc            = edge_info["node1_policy"]["min_htlc"],
                    fee_base_msat       = edge_info["node1_policy"]["fee_base_msat"],
                    fee_rate_milli_msat  = edge_info["node1_policy"]["fee_rate_milli_msat"]))
        # if("node2_policy" in edge_info):
        if(edge_info["node2_policy"] != None):
            new_entries_policies.append(Node_Policy(date_logged = edge_date,
                node =  nodes_entries[edge_info["node2_pub"]],
                channel =new_chans[index],
                time_lock_delta         = edge_info["node2_policy"]["time_lock_delta"],
                min_htlc                = edge_info["node2_policy"]["min_htlc"],
                fee_base_msat           = edge_info["node2_policy"]["fee_base_msat"],
                fee_rate_milli_msat     = edge_info["node2_policy"]["fee_rate_milli_msat"]))
        index+=1
    new_entries_policies = Node_Policy.objects.bulk_create(new_entries_policies)
    return new_chan_entries, new_entries_policies



def createDBentries(full_data_path):
    nodes_entries = {}
    edges_entries = []
    policy_entries= []
    dataFiles = getFiles(full_data_path,1) #One per day
    index=0
    print("have to process: "+ str(len(dataFiles)) + " files")

    for file in dataFiles:
        index+=1
        try:
            date,nodes,chans = getNetworkData(file)
            # print("Got file: " + file + "\twith " + str(len(nodes)) + " nodes\t"+str(len(chans)) + " channels")

            node_extra_info = [getCapacity(node["pub_key"],chans) for node in nodes]
            nodes_entries, address_entries = createNodeEntries(nodes,date,[ x for [x,y] in node_extra_info ] , [ y for [x,y] in node_extra_info ] )
            # for node in nodes:
            #     node_chans,node_capacity = getCapacity(node["pub_key"],chans)
            #     nodes_entries[node["pub_key"]] =createNodeEntry(node,date,node_chans,node_capacity) #May be a list

            edges_entries, policies = createChanEntries(chans,date,nodes_entries)

            print("[ "+ str(index) + "/" +  str(len(dataFiles)) + " ]\t"+"Created entries for "+ str(len(nodes_entries)) + " nodes and " + str(len(edges_entries)) + " channels " + " date:" + date.strftime("%Y-%m-%d %H:%M:%S") )
        except Exception as e:
            print("[ "+ str(index) + "/" +  str(len(dataFiles)) + " ]\t" + "ERROR ON FILE: " + file + " \t" + str(e))


def populate_db():
    if(input("Are you sure you want to rebuild the database? [y/n] ") == "y"):
        print("Removing existing entries")
        print(Node.objects.all().delete())    #TODO REMOVE, ONLY USE FOR TESTING
        print(Channel.objects.all().delete()) #TODO REMOVE, ONLY USE FOR TESTING

    if(input("Add new entries? [y/n] ") == "y"):
        createDBentries(data_location)

'''
#For use in django shell
pathScript ="/mnt/d/OneDrive/542_MSc_Indivdual_Project/misc/DataBasePopulate.py"
exec(open(pathScript).read())

scriptName = "DataBasePopulate.py"
exec(open(scriptName).read())
'''