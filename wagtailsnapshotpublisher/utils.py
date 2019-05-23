"""
.. module:: wagtailsnapshotpublisher.utils
"""

from functools import reduce  # forward compatibility for Python 3
import operator


def get_from_dict(data_dict, map_list):
    """ get_from_dict """
    return reduce(operator.getitem, map_list, data_dict)


def set_in_dict(data_dict, map_list, value):
    """ set_in_dict """
    get_from_dict(data_dict, map_list[:-1])[map_list[-1]] = value


def del_in_dict(data_dict, map_list):
    """ del_in_dict """
    del get_from_dict(data_dict, map_list[:-1])[map_list[-1]]


def get_dynamic_element_keys(data, keys=[], key=None, result=[]):
    """ get_dynamic_element_keys """
    keys_cp = keys.copy()

    if key is None:
        result = list()

    if key is not None and (
            isinstance(data, dict) or isinstance(data, list) or isinstance(data, tuple)):
        keys_cp.append(key)

    if isinstance(data, dict):
        for k, item in data.items():
            get_dynamic_element_keys(item, keys_cp, k, result)
    elif isinstance(data, list) or isinstance(data, tuple):
        for i, item in enumerate(data):
            get_dynamic_element_keys(item, keys_cp, i, result)
    else:
        if key == 'dynamic' and data:
            result.append(keys_cp)

    if key is None:
        return result
