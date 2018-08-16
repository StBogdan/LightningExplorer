# Helper methods for displaying lnd node data
# Bogdan Stoicescu (bs5017)
# Taken from the lnd developer reference
# https://api.lightning.community/

import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc
import os
import codecs
import json
import urllib.request
from  terminal_colours import *
from pickleUtils import save_obj,load_obj
import socket


from utils_config import *
def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_adr=(s.getsockname()[0])
    s.close()
    return ip_adr

#Setup
# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handhsake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

# Lnd cert is at ~/.lnd/tls.cert on Linux and
# ~/Library/Application Support/Lnd/tls.cert on Mac

# print("Opening secure channel to server")
# cert = open(os.path.expanduser(site_config["server_files"]+'/tls.cert'), 'rb').read()
# creds = grpc.ssl_channel_credentials(cert)
# channel = grpc.secure_channel('159.89.11.83:10009', creds)
# stub = lnrpc.LightningStub(channel)
#
#
# # Lnd admin macaroon is at ~/.lnd/admin.macaroon on Linux and
# # ~/Library/Application Support/Lnd/admin.macaroon on Mac
# with open(os.path.expanduser(site_config["server_files"]+'/admin.macaroon'), 'rb') as f:
#     macaroon_bytes = f.read()
#     macaroon = codecs.encode(macaroon_bytes, 'hex')

def get_info_dict(stub,macaroon):
    # Retrieve and display the wallet balance
    response = stub.GetInfo(ln.GetInfoRequest(),metadata = [('macaroon',macaroon)])
    # responseWallet = stub.WalletBalance(ln.WalletBalanceRequest(),metadata = [('macaroon',macaroon)])

    return response

def getInfo(stub,macaroon):
    # Retrieve and display the wallet balance
    response = stub.GetInfo(ln.GetInfoRequest(),metadata = [('macaroon',macaroon)])
    responseWallet = stub.WalletBalance(ln.WalletBalanceRequest(),metadata = [('macaroon',macaroon)])

    network = "[Mainnet]"
    if( response.testnet):
        network = "[Testnet]"

    descriptionStr = termPrint("Alias: ",bcolors.OKGREEN) + termPrint(response.alias, bcolors.BOLD) +"\t\t"+ termPrint("Pubkey: ",bcolors.OKGREEN) + str(response.identity_pubkey) + "\n"
    statusStr= termPrint("Channels:",bcolors.OKGREEN) + str(response.num_active_channels) + "("+ str(response. num_pending_channels) + ")\t" + termPrint("Peers:",bcolors.OKGREEN) + str(response.num_peers) + "\t"+ termPrint("Height:", bcolors.OKGREEN) + str(response.block_height) + "\t"+ termPrint("Balance:", bcolors.OKGREEN )+ str(responseWallet.total_balance) + " ("+ str(responseWallet.confirmed_balance) + ":" + str(responseWallet.unconfirmed_balance) +") SAT\t" + termPrint(network,bcolors.OKGREEN)

    return descriptionStr + statusStr

# https://api.lightning.community/#listpeers
def getPeers(stub,macaroon):
    responsePeers = stub.ListPeers(ln.ListPeersRequest(),metadata = [('macaroon',macaroon)])
    return responsePeers

def getPeerInfo(stub,macaroon):
    responsePeers = getPeers(stub,macaroon)
    peerStrings = "Currently connected to " + str(len(responsePeers.peers)) + " peers\n"
    for peer in responsePeers.peers:
        peerStrings+= peer.pub_key + "\t" + peer.address + "\t" + termPrint("Traffic: ",bcolors.OKGREEN)  + str(peer.sat_sent) + ":" + str(peer.sat_recv) + " SAT\t\t"
        peerStrings+="\n"

    return peerStrings

def getFeeReport(stub,macaroon):
     response = stub.FeeReport(ln.FeeReportRequest(), metadata=[('macaroon', macaroon)])
     return response

def getChannelString(chan):
    activityState = termPrint("[INACTIVE]", bcolors.WARNING)
    if(chan.active):
        activityState = termPrint("[ACTIVE]", bcolors.OKGREEN)
    # try:
    otherInfo =  getPubKeyInfo(chan.remote_pubkey)
    otherInfoString =  termPrint("Pubkey: ", bcolors.OKGREEN) + str(otherInfo["pub_key"]) + termPrint("\tAddress(es): ", bcolors.OKGREEN)

    for singleAdr in otherInfo["addresses"] :
        otherInfoString += str(singleAdr["addr"]) + " "

    return termPrint("ID: ", bcolors.OKGREEN) + termPrint(chan.chan_id, bcolors.BOLD) + " with "+ termPrint(getPubKeyName(chan.remote_pubkey),bcolors.BOLD) + "\n" + termPrint("Capacity: ", bcolors.OKGREEN) + str(chan.capacity) + " SAT\t" + termPrint("Balance: ", bcolors.OKGREEN) + str(chan.local_balance)+ ":"+ str(chan.remote_balance) +  " SAT\t" +  termPrint("Traffic: " , bcolors.OKGREEN)+ str(chan.total_satoshis_sent)+ ":"+ str(chan.total_satoshis_received) +  " SAT\t" + activityState +"\tUpdates: " + str(chan.num_updates) + "\n" + otherInfoString  + "\n" +  termPrint("ChanPoint: ", bcolors.OKGREEN) + str(chan.channel_point)
    # except Exception as e:
    #     return "Could not get channel: "+ str(e)

def getPubKeyName(pubkey):
    #Get the node alias
    #Uses the 1ml.com API
    try:
        url = "https://1ml.com/testnet/node/" + pubkey + "/json"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        return data["alias"]
    except Exception as e:
        # print("Error on pubkey:" + pubkey )
        return "UNKNOWN_ALIAS"


def getPubKeyInfo(pubkey):
    #Get the node alias
    #Uses the 1ml.com API
    try:
        url = "https://1ml.com/testnet/node/" + pubkey + "/json"
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        return data
    except Exception as e:
        return {"alias": "UNKNOWN_ALIAS" ,"pub_key" : pubkey , "addresses": []}

def getCurrentChannels(stub,macaroon):
    responseChannels = stub.ListChannels(ln.ListChannelsRequest(),metadata = [('macaroon',macaroon)])
    return responseChannels.channels

def getChannelStats(stub,macaroon):
    chan = getCurrentChannels(stub,macaroon)
    print("Displaying " + str(len(chan)) + " channels:")
    for chan in chan:
        print(getChannelString(chan))
        print("-------------------------------------------------------------------------------")

def getPendingChannels(stub,macaroon):
    response = stub.PendingChannels(ln.PendingChannelsRequest() ,metadata = [('macaroon',macaroon)])
    return response
     # {
     #     total_limbo_balance: <int64>,
     #     pending_open_channels: <PendingOpenChannel>,
     #     pending_closing_channels: <ClosedChannel>,
     #     pending_force_closing_channels: <ForceClosedChannel>,
     # }

def getPendingChannelStats(stub,macaroon):
    pending_chans = getPendingChannels(stub,macaroon)

    print("Displaying " + str(len(pending_chans.pending_open_channels)) + " pending open\t" + str(len(pending_chans.pending_closing_channels))  + " pending close\t"  + str(len(pending_chans.pending_force_closing_channels)) + " pending force close " + " channels:")
    for chan in pending_chans.pending_open_channels:
        print(getChannelStringPendOpen(chan))
        print("-------------------------------------------------------------------------------")
    for chan in pending_chans.pending_closing_channels:
        print(getPendingChannelStringPendClose(chan))
        print("-------------------------------------------------------------------------------")
    for chan in pending_chans.pending_force_closing_channels:
        print(getPendingChannelStringPendForceClose(chan))
        print("-------------------------------------------------------------------------------")

def getChannelStringPendOpen(chan):
    return str(chan)
def getPendingChannelStringPendClose(chan):
    return str(chan)
def getPendingChannelStringPendForceClose(chan):
    return str(chan)




def getNodeStats(stub,macaroon):
    return "TODO"

def getNetworkStats(stub,macaroon,get_raw=False):
    response = stub.DescribeGraph( ln.ChannelGraphRequest(),metadata = [('macaroon',macaroon)])
    if(get_raw):
        return response

    # Output reponse to file
    outFile = open('latest.graph', 'w')
    save_obj(response,"network_graph_data")
    outFile.write(str(response))
    print("Response object written to file")

    return "Got "+ str(len(response.nodes)) + " noodes and " + str(len(response.edges))+ " channels"

def startServerConnection(serverConfigDict):
    tls_cert_path=  serverConfigDict["tls_cert_path"]
    macaroon_path=  serverConfigDict["macaroon_path"]
    ip_port_adr=    serverConfigDict["ip_port_adr"]

    # print("Opening secure channel to server")
    cert = open(os.path.expanduser(tls_cert_path), 'rb').read()
    creds = grpc.ssl_channel_credentials(cert)

    with open(os.path.expanduser(macaroon_path), 'rb') as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, 'hex')

    channel = grpc.secure_channel(ip_port_adr, creds)
    stub = lnrpc.LightningStub(channel)

    return [stub,macaroon]

def getServerConfigs():
    #TODO Auto generate these based on the files in the folder
    serverList = [
            # {"Alias"      :"Local Ubuntu LND",
            # "ip_port_adr"   :getIP()+":10009",
            # "tls_cert_path" :'~/.lnd/tls.cert',
            # "macaroon_path" : '~/.lnd/admin.macaroon'},
            {"Alias"      :"Frankfurt-Connect",
            "pubkey"       :  "034f2330f7fca3a3eef0fad20b0d2aab09bbb7c960bfb59e02cd7100d234634af4",
            "ip_port_adr"   :"159.89.97.96:10009",
            "tls_cert_path" :site_config["server_files"]+'/frank1/tls.cert',
            "macaroon_path" : site_config["server_files"]+'/frank1/admin.macaroon'},
            {"Alias"      :"London-Connect",
            "pubkey"        : "02f82a1188bb4baa885de6c0d14276db056aa9da768de545c4fc7349379b5670cb",
            "ip_port_adr"   :"159.89.11.83:10009",
            "tls_cert_path" :site_config["server_files"]+'/london/tls.cert',
            "macaroon_path" : site_config["server_files"]+'/london/admin.macaroon'},
            {"Alias"      :"Lnd-San-Fran",
            "pubkey"        :  "02b9804133643b78aa6f6221284ddef81785f88f861931a3e574353e3a642c0f9f",
            "ip_port_adr"   :"159.89.133.236:10009",
            "tls_cert_path" :site_config["server_files"]+'/sanfran1/tls.cert',
            "macaroon_path" : site_config["server_files"]+'/sanfran1/admin.macaroon'}]
    return serverList

def getServerChoice(currentChoice):
    serverChoice = int(currentChoice)
    configSets= getServerConfigs()

    i=0
    for config in configSets:
        print("[" + str(i) + "] " + config["Alias"] + "\t\t" + config["ip_port_adr"])
        i+=1

    serverChoice = int(input("Select config set of " + str(len(configSets)) +" available: "))
    while(serverChoice <0 or serverChoice >= len(configSets)):
        print("Invalid option, please type in a number")
        serverChoice =int(input("Select config set of " + str(len(configSets)) +" available: "))

    return serverChoice


def getNodesWithIPs(networkGraph_nodes):
    nodesWithIPs = [node for node in networkGraph_nodes if  len(node["addresses"]) > 0 ]
    # node.pub_key == "023b14be2d7a3fc2b24eb14b25d44afc41cb8d0a6e01067da36ea3299e2f9bfe70"] #Testing with own node
    print("Counted notes with ip addresses: " + str(len(nodesWithIPs)))
    return nodesWithIPs

def getNodeURI(nodeInfo):
    if(len(nodeInfo["addresses"]) <1):
        print("ERROR: Node has no addresses")
        return ""
    else:
        return nodeInfo["pub_key"]+"@"+nodeInfo["addresses"][0]["addr"]
