from collections import Counter
from glob import glob
from pathlib import Path
import re
import tempfile
from typing import Any, Dict, Iterable, List, Mapping

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.docutils import SphinxDirective

from git import Repo


TRANSLATORS_MARKER_NAME = "# Translators:"


def grab_contributors(path: str) -> Iterable:
    found = False
    translators = set()
    with open(path, encoding="utf-8") as file:
        for line in file:
            if not found and TRANSLATORS_MARKER_NAME in line:
                found = True
                continue

            if found:
                line = line.strip("#\r\n ")

                if len(line) == 0:
                    break

                translators.add(re.search(r"(.*?)(,| <).*", line).group(1).title())

    return translators


def get_top_translators(translations_dir: str, locale: str) -> Mapping[str, int]:
    contributors = Counter()

    po_files = glob(str(Path(translations_dir) / "**" / locale / "**" / "*.po"), recursive=True)

    for file in po_files:
        contributors.update(grab_contributors(file))

    return contributors


class Contributor:
    def __init__(self, name, hide_contributions, contributions=0):
        self.name = name
        self.hide_contributions = hide_contributions
        self.contributions = contributions

    def build(self) -> nodes.Node:
        node_contributor = nodes.paragraph()
        node_contributor += nodes.Text(self.name)

        if not self.hide_contributions:
            node_contributor += nodes.Text(
                " - "
                + str(self.contributions)
                + " "
                + ("contributions" if self.contributions != 1 else "contribution")
            )
        return node_contributor


class ContributorSource:
    def __init__(self, contributors, limit=10):
        self.contributors = contributors
        self.limit = limit

    def build(self) -> nodes.Node:
        node_list = nodes.bullet_list()
        for idx, contributor in enumerate(self.contributors):
            if idx == self.limit:
                break
            node_contributor = nodes.list_item()
            node_contributor += contributor.build()
            node_list += node_contributor


        return node_list


class TopTranslators(SphinxDirective):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "limit": directives.positive_int,
        "locale": directives.unchanged_required,
        "order": directives.unchanged,
        "hide_contributions": directives.unchanged,
    }

    def run(self) -> List[nodes.Node]:
        limit: int = self.options.get("limit", 10)
        order: str = self.options.get("order", "alphabetical").lower()
        locale: str = self.options.get("locale")
        hide_contributions: bool = "true" in self.options.get(
            "hide_contributions", "false"
        ).lower()

        with tempfile.TemporaryDirectory() as temp_dir:

            repo_url = f"https://github.com/{self.arguments[0]}.git"

            # Clone repo
            try:
                Repo.clone_from(repo_url, temp_dir)
            except Exception as e:
                raise ExtensionError("Invalid git repository given!", e)

            contributors = get_top_translators(temp_dir, locale)
            alphabetical = "alphabetical" in order

            return [
                ContributorSource(
                    [
                        Contributor(name, hide_contributions, contributions)
                        for name, contributions in sorted(
                            contributors.items(),
                            key=lambda tup: tup[0] if alphabetical else tup[1],
                            reverse=not alphabetical,
                        )
                    ],
                    limit=limit,
                ).build()
            ]


def setup(app: Sphinx) -> Dict[str, Any]:
    directives.register_directive("toptranslators", TopTranslators)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": False,
    }
