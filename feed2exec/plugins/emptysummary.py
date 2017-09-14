def filter(*args, feed=None, entry=None, **kwargs):
    '''example of fixes for a broken feed, in this case, the GitHub
    release feed which (sometimes) sends empty contents.'''

    if entry:
        values = [x.value for x in entry.get('content', []) if x.value]
        if not values and not entry.get('summary'):
            entry['summary'] = entry.get('link')
