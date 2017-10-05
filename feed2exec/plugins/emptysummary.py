def filter(*args, feed=None, item=None, **kwargs):
    '''example of fixes for a broken feed, in this case, the GitHub
    release feed which (sometimes) sends empty contents.'''

    if item:
        values = [x.value for x in item.get('content', []) if x.value]
        if not values and not item.get('summary'):
            item['summary'] = item.get('link')
