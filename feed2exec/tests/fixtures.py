import pytest

from feed2exec.controller import FeedManager
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


# XXX: maybe merge with the feedmanager fixture?
@pytest.fixture()
@pytest.mark.usefixtures('betamax_session')
def betamax(betamax_session):
    assert betamax_session
    FeedManager.sessionConfig(betamax_session)
    FeedManager._session = betamax_session
    return betamax_session
