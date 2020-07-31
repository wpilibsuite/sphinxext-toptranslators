import pytest
import docutils.nodes as nodes
import re
from sphinxext.toptranslators import strip_accents


@pytest.mark.sphinx("html", testroot="limit")
def test_limit(html_contexts):
    assert len(list(html_contexts[0].doctree.traverse(nodes.list_item))) == 4


@pytest.mark.sphinx("html", testroot="hide-contributions-true")
def test_contributions_true(html_contexts):
    assert "contributions" not in html_contexts[0].doctree.astext()


@pytest.mark.sphinx("html", testroot="hide-contributions-false")
def test_contributions_false(html_contexts):
    assert "contributions" in html_contexts[0].doctree.astext()


@pytest.mark.sphinx("html", testroot="order-ranked")
def test_order_ranked(html_contexts):
    items = html_contexts[0].doctree.traverse(nodes.list_item)
    num_contributions = 1e99

    for item in items:
        num = int(re.search(r"(.*) - (.*?) contribution", item.astext()).group(2))
        assert num <= num_contributions
        num_contributions = num


@pytest.mark.sphinx("html", testroot="order-alphabetical")
def test_order_alphabetical(html_contexts):
    items = html_contexts[0].doctree.traverse(nodes.list_item)
    prev_name = None

    for item in items:
        name = re.search(r"(.*) - (.*?) contribution", item.astext()).group(1)
        name = strip_accents(name)
        if prev_name == None:
            prev_name = name
            continue

        assert name >= prev_name
        prev_name = name
