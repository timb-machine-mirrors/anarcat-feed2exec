def filter(*args, feed=None, item=None, **kwargs):
    '''the droptitle filter will drop any feed item with a title matching
    the given args
    '''
    feed['skip'] = ' '.join(args) in feed.get('title', '')
