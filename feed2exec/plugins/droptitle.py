def filter(*args, feed=None, entry=None, **kwargs):
    '''the droptitle filter will drop any feed entry with a title matching
    the given args
    '''
    feed['skip'] = ' '.join(args) in feed.get('title', '')
