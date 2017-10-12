def filter(*args, feed=None, item=None, **kwargs):
    '''example of fixes for a broken feed, in this case, the GitHub
    release feed which (sometimes) sends empty contents, in which case
    the item link field is used as a summary instead.
    '''

    if item:
        values = [x.value for x in item.get('content', []) if x.value]
        if not values and not item.get('summary'):
            item['summary'] = item.get('link')
