import os
import json
import codecs
import os.path as path

"""
What: Gets the config for the given site, from the file django_config
    Some unused methods for renaming files
Why: Middleware for configuration, if we're going to be putting this is docker/kubernetes/container magic
"""
def get_site_config():
    site_config = json.loads(codecs.open(os.environ["LNDMON_django_config"], 'r').read())
    if site_config["node_network"] != "mainnet" and site_config["node_network"] != "testnet":
        raise Exception("Invalid local network setting, set the string to 'mainnet' or 'testnet'")
    return site_config


def fix_date_string(folder_path=os.getcwd()):
    # Check that we are modifying the right files
    for fileName in os.listdir(folder_path):
        if fileName.startswith("2018-") and (
                fileName.endswith(".graph") or fileName.endswith(".netinfo")) and fileName.replace(":",
                                                                                                   "-") != fileName:
            print("RENAME:\t" + fileName + "\t-->\t" + fileName.replace(":", "-"))
            os.rename(folder_path + os.sep + fileName, folder_path + os.sep + fileName.replace(":", "-"))
        # else:
        # print("RENAME:\tFile " +fileName+ "\tnot eligible for rename")


def fix_dataset(folder_path=os.getcwd()):
    """ Do a rename of the data files in the given folder
    Check that files are of the required format, then renames
    """
    for dayDir in os.listdir(folder_path):
        if os.path.isdir(path.join(folder_path, dayDir)):
            print("Fixing folder\t" + dayDir)
            fix_date_string(folder_path + os.sep + dayDir)


def fix_date_string_folder(data_path):
    for fileName in os.listdir(data_path):
        # Check that we are modifying the right files
        # Check year and length
        if (fileName.startswith("18") and len(fileName) == 6 and os.path.isdir(
                path.join(data_path, fileName))):
            new_name = "2018-" + fileName[2:4] + "-" + fileName[4:6]
            print("RENAME:\t" + fileName + "\t-->\t" + new_name)
            os.rename(path.join(os.getcwd(),fileName), path.join(os.getcwd(), new_name))
        else:
            print("RENAME:\tFile " + fileName + "\tnot eligible for rename")
