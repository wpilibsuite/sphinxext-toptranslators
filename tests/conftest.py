from collections import namedtuple

import pytest
from sphinx.testing.path import path

pytest_plugins = "sphinx.testing.fixtures"


@pytest.fixture(scope="session")
def rootdir():
    return path(__file__).parent.abspath() / "roots"


@pytest.fixture()
def content(app):
    app.build()
    yield app


@pytest.fixture()
def html_contexts(app):
    HPCData = namedtuple(
        "HPCData", ["app", "pagename", "templatename", "context", "doctree"]
    )
    data = []

    def html_page_context(app, pagename, templatename, context, doctree):
        if doctree != None:
            data.append(HPCData(app, pagename, templatename, context, doctree))

    app.connect("html-page-context", html_page_context)
    app.build()
    return data


def pytest_configure(config):
    config.addinivalue_line("markers", "sphinx")
