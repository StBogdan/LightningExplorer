# Class for pretty printing on terminal output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def termPrint(text, style):
    return style + str(text) + bcolors.ENDC


def termDictPrint(dictionary, indent=0):
    dict_string = ""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            valueStr = termDictPrint(value, indent + 1)
        else:
            valueStr = str(value)
        dict_string += f"\n" + '\t' * indent + termPrint(key, bcolors.WARNING) + ": " + valueStr
    return dict_string
