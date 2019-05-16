from functools import reduce  # forward compatibility for Python 3
import operator


def getFromDict(dataDict, mapList):
    return reduce(operator.getitem, mapList, dataDict)


def setInDict(dataDict, mapList, value):
    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value


def delInDict(dataDict, mapList):
    del(getFromDict(dataDict, mapList[:-1])[mapList[-1]])


def get_dynamic_element_keys(data, keys=[], key=None, result=[]):
    keys_cp = keys.copy()

    if key is None:
        result = list()

    if key is not None and (isinstance(data, dict) or isinstance(data, list) or isinstance(data, tuple)):
        keys_cp.append(key)

    if isinstance(data, dict):
        for k, item in data.items():
            get_dynamic_element_keys(item, keys_cp, k, result)
    elif isinstance(data, list) or isinstance(data, tuple):
        for i in range(len(data)):
            get_dynamic_element_keys(data[i], keys_cp, i, result)
    else:
        if key=='dynamic' and data:
            result.append(keys_cp)

    if key is None:
        return result
