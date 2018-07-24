#Some functions and utility calls for lndmon.com
#Bogdan Stoicescu (bs5017)
import utils_metrics as metrics
from nodes.models import Metric
import os

def get_metric_info(file):
    if file == "metric_testnet_avg_chan_size.png":
        return "Average Channel Size", "In Satoshis, how big is your average channel, returned by 'getNetworkInfo'", metrics.generate_and_save("testnet_avg_chan_size")
    elif file == "metric_testnet_network_capacity.png":
        return "Network capacity", "Total network capacity, in BTC (10^8 or 100 000 000 SAT)", metrics.generate_and_save("testnet_network_capacity")
    elif file == "metric_testnet_nr_nodes_chans.png":
        return "Network presence","Number of nodes with open channels compared to the total number of nodes",metrics.generate_and_save("testnet_nr_nodes_chans")
    elif file == "metric_testnet_avg_degree.png":
        return "Average number of channels per node","Showing both the average and the maximum number of channels per node.\nKeep in mind that a significant proportion of nodes do not have open channels", metrics.generate_and_save("testnet_avg_degree")
    elif file == "metric_testnet_nodes_with_chans.png":
        return "Proportion of nodes with channels","The situation is looking more interesting on the mainnet, where the number of channels exceeds the number of nodes, though more data needs to be collected", metrics.generate_and_save("testnet_nodes_with_chans")
    elif file == "metric_testnet_locations.png":
        return "Global distribution of nodes","Based on a location search for the advertised IPs", metrics.generate_and_save("testnet_locations")
    else:
        return "Network statictic","This show a statistic for the network, more information coming soon",""


def db_put_metrics(metric_filenames,file_path_prefix):
    for metric_file in metric_filenames:
        # os.getcwd()+os.sep +
        imageSource =  file_path_prefix + os.sep+ metric_file
        metric_title, metric_desc, metric_dataset_url = get_metric_info(metric_file)
        newMetric = Metric( image_url = imageSource,
                            title =metric_title,
                            description=metric_desc,
                            dataset_url =metric_dataset_url)
        newMetric.save()
        print("Put metric in database")

def db_update_metrics():
    db_put_metrics(os.listdir("media"),"media")
