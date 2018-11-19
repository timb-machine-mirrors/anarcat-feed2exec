import pytest

from feed2exec.feeds import (FeedManager, Feed)
import feed2exec.plugins.maildir


@pytest.fixture()
def feed_manager(tmpdir_factory):
    conf_path = tmpdir_factory.mktemp('config').join('feed2exex.ini')
    db_path = tmpdir_factory.mktemp('db').join('feed2exec.db')
    return FeedManager(str(conf_path), str(db_path))


@pytest.fixture(autouse=True)
def static_boundary(monkeypatch):
    monkeypatch.setattr(feed2exec.email, 'boundary',
                        '===============testboundary==')


@pytest.fixture()
@pytest.mark.usefixtures('betamax_session')
def betamax(betamax_session):
    assert betamax_session
    Feed.sessionConfig(betamax_session)
    Feed._session = betamax_session
    return betamax_session


# cargo-culted from Monkeysign
def skipUnlessNetwork():
    """add a knob to disable network tests

    to disable network tests, use PYTEST_USENETWORK=no. by default, it
    is assumed there is network access.

    this is mainly to deal with Debian packages that are built in
    network-less chroots. unfortunately, there is no standard
    environment in dpkg-buildpackage or ./debian/rules binary that we
    can rely on to disable tests, so we revert to a custom variable
    that can hopefully make it up to the pybuild toolchain

    I looked at DEB_BUILD_OPTIONS=network, but that is not standard
    and only mentionned once here:

    https://lists.debian.org/debian-devel/2009/09/msg00992.html

    DEB_BUILD_OPTIONS is also not set by default, so it's not a good
    way to detect Debian package builds

    pbuilder uses USENETWORK=no/yes, schroot uses UNSHARE_NET, but
    those are not standard either, see:

    https://github.com/spotify/dh-virtualenv/issues/77
    https://github.com/codelibre-net/schroot/blob/2e3d015a759d2b5106e851af34c8d5974d84f18e/lib/schroot/chroot/facet/unshare.cc
    """

    if ('PYTEST_USENETWORK' in os.environ
       and 'no' in os.environ.get('PYTEST_USENETWORK', '')):
        return unittest.skip('network tests disabled (PYTEST_USENETWORK=no)')
    else:
        return lambda func: func
