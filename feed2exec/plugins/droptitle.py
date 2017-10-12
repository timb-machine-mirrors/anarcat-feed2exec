def filter(*args, feed=None, item=None, **kwargs):
    '''the droptitle filter will drop any feed item with a title matching
    the given args.

    Example::

      [NASA breaking news]
      url = https://www.nasa.gov/rss/dyn/breaking_news.rss
      filter = feed2exec.plugins.droptitle
      filter_args = Trump

    The above will process the feed items according to the global
    configuration, but will skip any item that has the word "Trump"
    anywhere in the title field.
    '''
    item['skip'] = ' '.join(args) in item.get('title', '')
