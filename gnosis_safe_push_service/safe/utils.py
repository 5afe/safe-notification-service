def remove_null_values(obj):
    """
    Remove all null values from a dictionary
    :param obj: dictionary
    :return: filtered dictionary
    """
    if not isinstance(obj, dict):
        return obj

    for k in list(obj.keys()):
        _obj = obj[k]
        if _obj is None:
            del obj[k]
        elif isinstance(obj[k], dict):
            remove_null_values(obj[k])

    return obj


def add_0x_prefix(value):
    return '0x' + value if value[:2] not in (b'0x', '0x') else value
