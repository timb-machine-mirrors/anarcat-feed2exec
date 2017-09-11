#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

import html
import json

from click.testing import CliRunner

import feed2exec.utils as utils
from feed2exec.__main__ import main
import feed2exec.plugins.html2text as html2text_plugin
from feed2exec.tests.test_feeds import (ConfFeedStorage, test_data,
                                        test_nasa)


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0


def test_basics(tmpdir_factory):
    conf_dir = tmpdir_factory.mktemp('main')
    conf_path = conf_dir.join('feed2exec.ini')
    ConfFeedStorage.path = str(conf_path)
    runner = CliRunner()
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add',
                                  test_data['name'],
                                  test_data['url']])
    assert conf_dir.join('feed2exec.ini').check()
    assert result.exit_code == 0
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'ls'])
    assert result.exit_code == 0
    del test_data['output_args']
    del test_data['output']
    assert result.output.strip() == json.dumps(test_data,
                                               indent=2,
                                               sort_keys=True)
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'rm', 'test'])
    assert result.exit_code == 0
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'ls'])
    assert result.exit_code == 0
    assert result.output == ""

    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add',
                                  test_nasa['name'],
                                  test_nasa['url']])
    assert conf_dir.join('feed2exec.ini').check()
    assert result.exit_code == 0

    maildir = conf_dir.join('maildir')
    test_path = utils.find_test_file('planet-debian.xml')
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add', 'planet-debian',
                                  'file://' + test_path,
                                  '--output', 'feed2exec.plugins.maildir',
                                  '--output_args',
                                  str(maildir) + ' to@example.com',
                                  '--filter', 'feed2exec.plugins.html2text'])
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'fetch'])
    assert result.exit_code == 0
    assert maildir.check()
    for path in maildir.join('planet-debian').join('new').visit():
        body = path.read()
        if 'Marier' in body:
            break
    else:
        assert False, "entry from Francois Marier not found"

    with open(test_path) as xml:
        data = "".join(xml.readlines()[60:143])
        data = data.replace("     <description>", '')
        data = data.replace("</description>", '')
    expected = '''Date: Sat, 09 Sep 2017 04:52:47 -0000
To: to@example.com
From: planet-debian <to@example.com>
Subject: =?utf-8?q?Fran=C3=A7ois_Marier=3A_TLS_Authentication_on_Freenode_and_OFTC?=
Message-ID: http-feeding-cloud-geek-nz-posts-tls_authentication_freenode_and_oftc
User-Agent: feed2exec (???)
Precedence: list
Auto-Submitted: auto-generated
Archive-At: http://feeding.cloud.geek.nz/posts/tls_authentication_freenode_and_oftc/
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

http://feeding.cloud.geek.nz/posts/tls_authentication_freenode_and_oftc/

%s''' % html2text_plugin.filter.parse(html.unescape(data))  # noqa
    assert expected == body
