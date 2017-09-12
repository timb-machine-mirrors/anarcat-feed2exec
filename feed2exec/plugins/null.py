def output(*args, **kwargs):
    """
    This plugin does nothing. It can be useful in cases where you want
    to catchup with imported feeds.
    """
    pass


def filter(entry=None, *args, **kwargs):
    """
    The null filter removes all elements from a feed item
    """
    for i in entry:
        entry[i] = None
