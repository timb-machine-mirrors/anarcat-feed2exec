import pytest

from feed2exec.controller import FeedManager
import feed2exec.plugins.maildir


@pytest.fixture()
@pytest.mark.usefixtures('betamax_session')
def feed_manager(tmpdir_factory, betamax_session):
    conf_path = tmpdir_factory.mktemp('config').join('feed2exex.ini')
    db_path = tmpdir_factory.mktemp('db').join('feed2exec.db')
    return FeedManager(str(conf_path), str(db_path), session=betamax_session)


@pytest.fixture(autouse=True)
def static_boundary(monkeypatch):
    monkeypatch.setattr(feed2exec.email, 'boundary',
                        '===============testboundary==')
