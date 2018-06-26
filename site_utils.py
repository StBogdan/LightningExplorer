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
