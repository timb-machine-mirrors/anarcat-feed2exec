from collections import defaultdict
from typing import DefaultDict

feed_item_url_set: DefaultDict[str, set] = defaultdict(set)


def filter(feed=None, item=None, *args, **kwargs):
    """
    The unique filter skips URLs it has already seen in this run.
    """
    if item['link'] in feed_item_url_set[feed.name]:
        item['skip'] = True
        return None
    feed_item_url_set[feed.name].add(item['link'])
