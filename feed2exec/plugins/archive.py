import logging
import os.path
import requests
from feed2exec.utils import slug, make_dirs_helper


#: default archive directory
DEFAULT_ARCHIVE_DIR = '/run/user/1000/'


def output(*args, feed=None, item=None, session=None, **kwargs):
    """The archive plugin saves the feed's item.link URLs into a
    directory, specified by DEFAULT_ARCHIVE_DIR or through the output
    `args` value.

    Example::

      [NASA breaking news]
      url = https://www.nasa.gov/rss/dyn/breaking_news.rss
      output = archive
      args = /srv/archive/nasa/

    The above will save the "NASA breaking news" into the
    ``/srv/archive/nasa`` directory. Do *not* use interpolation here
    as the feed's variable could be used to mount a directory
    transversal attack.
    """

    # make a safe path from the item name
    path = slug(item.get('title', 'no-name'))
    # take the archive dir from the user or use the default
    archive_dir = ' '.join(args) if args else DEFAULT_ARCHIVE_DIR
    make_dirs_helper(archive_dir)
    # put the file in the archive directory
    path = os.path.join(archive_dir, path)
    # only operate on items that actually have a link
    if item.get('link'):
        # tell the user what's going on, if verbose
        # otherwise, we try to stay silent if all goes well
        logging.info('saving feed item %s to %s from %s%s',
                     item.get('title'), path, item.get('link'),
                     feed.get('catchup', '') and ' (simulated)')
        if feed.get('catchup'):
            return True
        # fetch the URL in memory
        result = session.get(item.get('link'))
        if result.status_code != requests.codes.ok:
            logging.warning('failed to fetch link %s: %s',
                            item.get('link'), result.status_code)
            # make sure we retry next time
            return False
        # open the file
        with open(path, 'w') as archive:
            # write the response
            archive.write(result.text)
        return True
    else:
        logging.info('no link for feed item %s, not archiving',
                     item.get('title'))
        # still consider the item processed, as there's nothing to archive
        return True
