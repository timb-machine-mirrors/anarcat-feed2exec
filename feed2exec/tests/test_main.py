#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

import json

from click.testing import CliRunner

import feed2exec
import feed2exec.utils as utils
from feed2exec.__main__ import main
from feed2exec.tests.test_feeds import (ConfFeedStorage, test_sample,
                                        test_nasa)
from feed2exec.tests.fixtures import static_boundary  # noqa


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0


def test_basics(tmpdir_factory, static_boundary):  # noqa
    conf_dir = tmpdir_factory.mktemp('main')
    conf_path = conf_dir.join('feed2exec.ini')
    ConfFeedStorage.path = str(conf_path)
    runner = CliRunner()
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add',
                                  '--output', 'feed2exec.plugins.echo',
                                  test_sample['name'],
                                  test_sample['url']])
    assert conf_dir.join('feed2exec.ini').check()
    assert result.exit_code == 0
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'ls'])
    assert result.exit_code == 0
    del test_sample['args']
    assert result.output.strip() == json.dumps(test_sample,
                                               indent=2,
                                               sort_keys=True)
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'rm', test_sample['name']])
    assert result.exit_code == 0
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'ls'])
    assert result.exit_code == 0
    assert result.output == ""

    maildir = conf_dir.join('maildir')
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add',
                                  '--mailbox', str(maildir),
                                  test_nasa['name'],
                                  test_nasa['url']])
    assert conf_dir.join('feed2exec.ini').check()
    assert result.exit_code == 0

    test_path = utils.find_test_file('planet-debian.xml')
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add', 'planet-debian',
                                  'file://' + test_path,
                                  '--args', 'to@example.com',
                                  '--mailbox', str(maildir)])
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
    expected = '''Content-Type: multipart/alternative; boundary="===============testboundary=="
MIME-Version: 1.0
Date: Sat, 09 Sep 2017 04:52:47 -0000
To: to@example.com
From: planet-debian <to@example.com>
Subject: =?utf-8?q?Fran=C3=A7ois_Marier=3A_TLS_Authentication_on_Freenode_and_OFTC?=
Message-ID: http-feeding-cloud-geek-nz-posts-tls_authentication_freenode_and_oftc
User-Agent: feed2exec (%s)
Precedence: list
Auto-Submitted: auto-generated
Archive-At: http://feeding.cloud.geek.nz/posts/tls_authentication_freenode_and_oftc/

--===============testboundary==
Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

<p>In order to easily authenticate with IRC networks such as
<a href=3D"https://www.oftc.net/NickServ/CertFP/">OFTC</a> and
<a href=3D"https://freenode.net/kb/answer/certfp">Freenode</a>, it is possi=
ble to use
<em>client TLS certificates</em> (also known as <em>SSL certificates</em>).=
 In fact, it
turns out that it's very easy to setup both on <a href=3D"https://irssi.org=
/">irssi</a>
and on <a href=3D"https://wiki.znc.in/">znc</a>.</p>

<h1 id=3D"Generate_your_TLS_certificate">Generate your TLS certificate</h1>

<p>On a machine with <a href=3D"http://altusmetrum.org/ChaosKey/">good entr=
opy</a>, run the
following command to create a keypair that will last for 10 years:</p>

<pre><code>openssl req -nodes -newkey rsa:2048 -keyout user.pem -x509 -days=
 3650 -out user.pem -subj "/CN=3D&lt;your nick&gt;"
</code></pre>

<p>Then extract your key fingerprint using this command:</p>

<pre><code>openssl x509 -sha1 -noout -fingerprint -in user.pem | sed -e 's/=
^.*=3D//;s/://g'
</code></pre>

<h1 id=3D"Share_your_fingerprints_with_NickServ">Share your fingerprints wi=
th NickServ</h1>

<p>On each IRC network, do this:</p>

<pre><code>/msg NickServ IDENTIFY Password1!
/msg NickServ CERT ADD &lt;your fingerprint&gt;
</code></pre>

<p>in order to add your fingerprint to the access control list.</p>

<h1 id=3D"Configure_ZNC">Configure ZNC</h1>

<p>To configure znc, start by putting the key in the right place:</p>

<pre><code>cp user.pem ~/.znc/users/&lt;your nick&gt;/networks/oftc/moddata=
/cert/
</code></pre>

<p>and then enable the built-in <a href=3D"https://wiki.znc.in/Cert">cert p=
lugin</a> for
each network in <code>~/.znc/configs/znc.conf</code>:</p>

<pre><code>&lt;Network oftc&gt;
    ...
            LoadModule =3D cert
    ...
&lt;/Network&gt;
    &lt;Network freenode&gt;
    ...
            LoadModule =3D cert
    ...
&lt;/Network&gt;
</code></pre>

<h1 id=3D"Configure_irssi">Configure irssi</h1>

<p>For irssi, do the same thing but put the cert in <code>~/.irssi/user.pem=
</code> and
then change the OFTC entry in <code>~/.irssi/config</code> to look like thi=
s:</p>

<pre><code>{
  address =3D "irc.oftc.net";
  chatnet =3D "OFTC";
  port =3D "6697";
  use_tls =3D "yes";
  tls_cert =3D "~/.irssi/user.pem";
  tls_verify =3D "yes";
  autoconnect =3D "yes";
}
</code></pre>

<p>and the Freenode one to look like this:</p>

<pre><code>{
  address =3D "chat.freenode.net";
  chatnet =3D "Freenode";
  port =3D "7000";
  use_tls =3D "yes";
  tls_cert =3D "~/.irssi/user.pem";
  tls_verify =3D "yes";
  autoconnect =3D "yes";
}
</code></pre>

<p>That's it. That's all you need to replace password authentication with a
much stronger alternative.</p>
--===============testboundary==
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable

http://feeding.cloud.geek.nz/posts/tls_authentication_freenode_and_oftc/

In order to easily authenticate with IRC networks such as [OFTC][1] and
[Freenode][2], it is possible to use _client TLS certificates_ (also known =
as
_SSL certificates_). In fact, it turns out that it's very easy to setup both
on [irssi][3] and on [znc][4].

   [1]: <https://www.oftc.net/NickServ/CertFP/>

   [2]: <https://freenode.net/kb/answer/certfp>

   [3]: <https://irssi.org/>

   [4]: <https://wiki.znc.in/>

# Generate your TLS certificate

On a machine with [good entropy][5], run the following command to create a
keypair that will last for 10 years:

   =20
       [5]: <http://altusmetrum.org/ChaosKey/>

    openssl req -nodes -newkey rsa:2048 -keyout user.pem -x509 -days 3650 -=
out user.pem -subj "/CN=3D<your nick>"
   =20

Then extract your key fingerprint using this command:

   =20
   =20
    openssl x509 -sha1 -noout -fingerprint -in user.pem | sed -e 's/^.*=3D/=
/;s/://g'
   =20

# Share your fingerprints with NickServ

On each IRC network, do this:

   =20
   =20
    /msg NickServ IDENTIFY Password1!
    /msg NickServ CERT ADD <your fingerprint>
   =20

in order to add your fingerprint to the access control list.

# Configure ZNC

To configure znc, start by putting the key in the right place:

   =20
   =20
    cp user.pem ~/.znc/users/<your nick>/networks/oftc/moddata/cert/
   =20

and then enable the built-in [cert plugin][6] for each network in
`~/.znc/configs/znc.conf`:

   =20
       [6]: <https://wiki.znc.in/Cert>

    <Network oftc>
        ...
                LoadModule =3D cert
        ...
    </Network>
        <Network freenode>
        ...
                LoadModule =3D cert
        ...
    </Network>
   =20

# Configure irssi

For irssi, do the same thing but put the cert in `~/.irssi/user.pem` and th=
en
change the OFTC entry in `~/.irssi/config` to look like this:

   =20
   =20
    {
      address =3D "irc.oftc.net";
      chatnet =3D "OFTC";
      port =3D "6697";
      use_tls =3D "yes";
      tls_cert =3D "~/.irssi/user.pem";
      tls_verify =3D "yes";
      autoconnect =3D "yes";
    }
   =20

and the Freenode one to look like this:

   =20
   =20
    {
      address =3D "chat.freenode.net";
      chatnet =3D "Freenode";
      port =3D "7000";
      use_tls =3D "yes";
      tls_cert =3D "~/.irssi/user.pem";
      tls_verify =3D "yes";
      autoconnect =3D "yes";
    }
   =20

That's it. That's all you need to replace password authentication with a mu=
ch
stronger alternative.


--===============testboundary==--
''' % (feed2exec.__version__)  # noqa
    assert expected == body
