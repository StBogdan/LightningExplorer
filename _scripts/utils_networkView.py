import json
import os
import time
from random import shuffle

import rpc_pb2 as ln
import thunder
from _scripts import utils_databasePopulate as Db_pop
from terminal_colours import bcolors
from terminal_colours import term_print

os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'
graphDataFileStr = "latest.graph"
min_chan_size = 20000  # SAT
our_chan_size = 400000  # To Try to create channels

"""
What:  Connect to all connect-able nodes
Why: Help maintain a full view of the network
"""


def open_chan_with_node(node):
    request_channel_open = ln.OpenChannelRequest(
        node_pubkey=node.pub_key.decode("hex"),
        node_pubkey_string=node.pub_key,
        local_funding_amount=our_chan_size,
        push_sat=0,
        target_conf=0,
        sat_per_byte=1,  # Give some fee to miners
        private=0,
        min_htlc_msat=0,
    )
    print("[NetView Upkeep] Attempting to open channel with " + term_print(node.pub_key, bcolors.WARNING))

    try:
        response = stub.OpenChannelSync(request_channel_open, metadata=[('macaroon', macaroon)])
        print(
            term_print("OPENED with TX:\t", bcolors.OKGREEN) + term_print(str(response.funding_txid_bytes.encode('hex')),
                                                                          bcolors.WARNING))
    except Exception as e:
        print(term_print("FAILED\t", bcolors.FAIL) + str(e.code()) + "\t" + str(e.details()))


def connectAllNodes(networkData_nodes, stub, macaroon):
    nodesToTry = thunder.getNodesWithIPs(networkData_nodes)
    requestedNodes = []
    failedNodes = []
    # nodesToTry = [x for x in nodesToTry if ((not x in connectedNodes) and (not x in failedNodes))]

    # Try to connect to clients
    index = 0
    for node in nodesToTry:
        currentTarget = ln.LightningAddress()
        currentTarget.pubkey = node["pub_key"]
        currentTarget.host = node["addresses"][0]["addr"]
        print("[NetView Upkeep][" + str(index) + "/" + str(len(nodesToTry)) + "] Target: " + term_print(
            thunder.getNodeURI(node), bcolors.WARNING))
        # print(termPrint(currentTarget,bcolors.WARNING))
        try:
            requestConnect = ln.ConnectPeerRequest(
                addr=currentTarget,  # Pubkey@ip:port #getNodeURI(nodeInfo)
                perm=True,  # Normal too slow due to generous timeouts
            )
            response = stub.ConnectPeer(requestConnect, metadata=[('macaroon', macaroon)])
            print(term_print("[NetView Upkeep] Request Sent\t", bcolors.OKGREEN) + str(response))
            requestedNodes.append(node)
        except Exception as e:
            if str(e.details()).startswith("already connected to peer"):
                print(term_print("ALREADY CONNECTED\t", bcolors.WARNING) + str(e.details()))
                requestedNodes.append(node)
            else:
                print(term_print("FAILED\t", bcolors.FAIL) + str(e.code()) + "\t" + str(e.details()))
                failedNodes.append(node)
        index += 1
    return [requestedNodes, failedNodes]


def connect_to_peer(peer_data):
    currentTarget = ln.LightningAddress()
    try:
        pk, host = peer_data.pub_key, peer_data.address
    except:
        pk, host = peer_data["pub_key"], peer_data["address"]

    currentTarget.pubkey = pk
    currentTarget.host = host
    print("[NetView Upkeep] Target: " + term_print(pk, bcolors.WARNING))
    try:
        requestConnect = ln.ConnectPeerRequest(
            addr=currentTarget,  # Pubkey@ip:port #getNodeURI(nodeInfo)
            perm=True,  # Normal too slow due to generous timeouts
        )
        response = stub.ConnectPeer(requestConnect, metadata=[('macaroon', macaroon)])
        print(term_print("[NetView Upkeep] Request Sent\t", bcolors.OKGREEN) + str(response))
        # connectedNodes.append(node)
    except Exception as e:
        if str(e.details()).startswith("already connected to peer"):
            print(term_print("ALREADY CONNECTED\t", bcolors.WARNING) + str(e.details()))
        else:
            print(term_print("FAILED\t", bcolors.FAIL) + str(e.code()) + "\t" + str(e.details()))


####################################################################

def connect_all_peers(graph_filePath, stub, macaroon):
    choice = str(input("[NetView Upkeep] Find new peers? "))
    if (choice == "y"):
        date, net_nodes, net_edges = Db_pop.get_net_data(graph_filePath)
        print("Obtained network data channels: " + str(len(net_nodes)) + " nodes and " + str(
            len(net_edges)) + " channels for date: " + str(date))

        connectAllNodes(net_nodes, stub, macaroon)
        print("Sent connection requests, waiting for 10s")
        time.sleep(10)

    # Remove nodes with which channels exist
    current_counter_parties = [chan.remote_pubkey for chan in thunder.getCurrentChannels(stub, macaroon)]
    current_pending_parties = [pending_chan.channel.remote_node_pub for pending_chan in
                             thunder.getPendingChannels(stub, macaroon).pending_open_channels]

    peerList = list(thunder.getPeers(stub, macaroon).peers)
    print("[NetView Upkeep] Currently connected to  " + str(len(peerList)) + " peers")
    choice = str(input("[NetView Upkeep] Save current peer list? "))
    if choice == "y":
        peer_file = open("datasets/amiable_peers", "w+")
        peer_file.write(json.dumps([{"pub_key": x.pub_key, "address": x.address} for x in peerList]))
        peer_file.close()

    choice = str(input("[NetView Upkeep] Connect to peers from memory? "))
    if choice == "y":
        saved_peer_data = json.loads(open("datasets/amiable_peers").read())
        print("[NetView Upkeep] Got " + str(len(saved_peer_data)) + " from memory ")

        for peer in saved_peer_data:
            connect_to_peer(peer)

    new_nodes = [node for node in peerList if
                not node.pub_key in current_counter_parties and not node.pub_key in current_pending_parties]

    print(term_print("Channels now:\t", bcolors.OKGREEN) + str(len(thunder.getCurrentChannels(stub, macaroon))))
    print(term_print("Channels soon:\t", bcolors.OKGREEN) + str(
        len(thunder.getPendingChannels(stub, macaroon).pending_open_channels)))
    print(term_print("Connected to:\t", bcolors.OKGREEN) + str(len(peerList)) + term_print("\tNew Peers:\t",
                                                                                           bcolors.OKGREEN) + str(
        len(new_nodes)))
    choice = str(input("[NetView Upkeep] Open new channels? "))
    if choice == "y":
        shuffle(new_nodes)
        for node in new_nodes:
            open_chan_with_node(node)


stub, macaroon = thunder.startServerConnection(thunder.getServerConfigs()[0])
graph_data_ftpath = "/Users/stbogdan/OneDrive/542_MSc_Indivdual_Project/Data/testing_mainnet/2018-08-01/2018-08-01-23-58-05.graph"
connect_all_peers(graph_data_ftpath, stub, macaroon)
