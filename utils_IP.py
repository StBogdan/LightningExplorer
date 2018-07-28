import json
import time
import sys
import urllib.request

# heat maps for client activity         (future)
#  displaying those within a timeline   (future)
#  data from hub nodes                  (mention HTLC output)
# - Uptime measurement of nodes         (measure by presence in network ?)
# - Geographical location               (current displayed)
# - Measured up/download bandwidth and latency (look into)
# - Client version number                       (Not given, see BOLT spec)
# - From each node that you have you should send a payment to all your other nodes and map the network if possible
# etc..

import pickle
# Pickle-based object saving methods
def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

def get_IP_location(ip):
    try:
        octets = ip.split(".")
        if(len(octets) != 4):
            return "Invalid IP address"
        for octet in octets:
            if(int(octet) < 0 and int(octet) > 255):
                return "Invalid IP address"
    except:
        return "Invalid IP Address"


    url = "http://ip-api.com/json/" + ip

    with urllib.request.urlopen(url) as openedURL:
        response = openedURL.read()
    query_result = json.loads(response.decode('utf-8'))
    time.sleep(0.75) #Server limit is 150 req per min, this time delay is conservative
    return query_result

# def savingTest():
#     dataDict["test"] = get_IP_location("test")
#
#     print("Got data dictionary " + str(dataDict))
#
#     save_obj(dataDict,"savedDict")
#     print("Saved obj")
#     newDataDict = load_obj("savedDict")
#     print("Recovered obj")
#     print(str(newDataDict))
#     print("test" in newDataDict)

def create_ip_dict(data_file_fpath):

    data = json.loads(open(data_file_fpath).read())
    print("Got data consisting of nodes:"+ str(len(data["nodes"])))

    try:
        location_data_dict = json.loads(open("datasets/cached_ip_data").read())
        print("[IP POZ] Got dictionary with keys " + str(len(location_data_dict)))
    except:
        location_data_dict= {}
        print("[IP POZ] Started new IP position dictionary as no cached available")

    print("[IP POZ] Started processing at "+ time.strftime("%H:%M:%S"))
    print("[IP POZ] Rate is 1 IP every 0.75s, total less than 11 mins for 900 addresses")

    index =0
    for node in data["nodes"]:
        # For any advertised addresses
        for nodeNetData in node["addresses"]:         #Each of advertised addresses
            if(len(nodeNetData["addr"].split(":")) > 2): #See if IPv6
                ip_str= nodeNetData["addr"].split("]")[0][1::] #Remove starting []
            else:
                ip_str = nodeNetData["addr"].split(":")[0] #Remove port
            # print("[Node "+ str(index)+ " of \t" + str(len(data["nodes"]))+"] Processing: " + ip_str)
            if(not ip_str in location_data_dict):
                location_data = get_IP_location(ip_str)
                # print("Got new location data:" + str(locationData) + "\n")
                if(location_data != "Invalid IP address" and not location_data["status"]== 'fail'):
                    location_data_dict[ip_str]= location_data #add to dict
                else:
                    location_data_dict[ip_str]="No data"
            else:
                pass
                # print("Got cached location data:" + str(location_data_dict[ip_str]) + "\n")
            index+=1
    print("[IP POZ] Got info for "+ str(index)+ " addresses")


    cache_file = open("datasets/cached_ip_data","w+")
    cache_file.write(json.dumps(location_data_dict))
    cache_file.close()

    return location_data_dict


if __name__ == "__main__":
    create_ip_dict(sys.argv[1]) #Get first argument as FULL PATH to data file
