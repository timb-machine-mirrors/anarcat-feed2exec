import logging
import os
import re
import subprocess
from unidecode import unidecode


from feed2exec.plugins.html2text import filter as html2text_filter


def sanitize(text, repl='-'):
    """like utils.slug, but without lowercase and allow custom replacement

    >>> sanitize('test')
    'test'
    >>> sanitize('../../../etc/password')
    'etc-password'
    >>> sanitize('Foo./.bar', repl='.')
    'Foo.bar'
    """
    return re.sub(r'\W+', repl, unidecode(text).strip()).strip(repl)


def output(hostname='localhost', *args,
           feed=None, item=None, **kwargs):
    """the transmission plugin will send feed items to a `transmission
    <http://www.transmissionbt.com/>`_ instance

    it assumes the ``transmission-remote`` command is already
    installed and configured to talk with transmission.

    the hostname is passed in the ``args`` configuration and defaults
    to localhost. the ``folder`` parameter is also used to determine
    where to save the actual torrents files.

    note that this will also append a sanitized version of the item
    title, if a folder is provided. this is to allow saving series in
    the same folder.

    if the title is unique for each torrent, you may use a filter to
    set the title to the right location.
    """
    command = ['transmission-remote', hostname, '-a', item['link']]
    if feed.get('folder', None):
        # sanitize title to avoid directory transversal
        subfolder = sanitize(item.get('title', ''), repl='.')
        path = os.path.join(feed['folder'], subfolder)
        command += ['-w', path]
    else:
        path = 'default path'
    logging.info('adding torrent "%s" to %s: %s%s',
                 item.get('title'), path,
                 html2text_filter.parse(item.get('summary')),
                 feed.get('catchup', '') and ' (simulated)')
    logging.debug("calling command %s%s", command,
                  feed.get('catchup', '') and ' (simulated)')
    if not feed.get('catchup'):
        subprocess.check_call(command)
    return True
