from collections import Counter
from glob import glob
import os
from pathlib import Path
import re
import shutil
import stat
from typing import Any, Dict, Iterable, List

from docutils import nodes
from docutils.parsers.rst import directives
from git import Repo
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError
from sphinx.util.docutils import SphinxDirective

from tempfile import mkdtemp
import unicodedata


TRANSLATORS_MARKER_NAME = "# Translators:"

CACHE = {}

# https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string/518232#518232
def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# Workaround due to git-python storing handles after program execution
def del_rw(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


# Delete directory if exists
def del_directory_exists(directory: str):
    dirpath = Path(directory)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath, onerror=del_rw)
    else:
        print("Directory does not exist!")

class TempDir:

    def __enter__(self):
        self.temp_dir = mkdtemp()
        return self.temp_dir

    def __exit__(self, exc_type, exc_value, exc_traceback):
        del_directory_exists(self.temp_dir)


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


def get_top_translators(translations_dir: str, locale: str) -> Counter:
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
    def __init__(self, contributors):
        self.contributors = contributors

    def build(self) -> nodes.Node:
        node_list = nodes.bullet_list()
        for contributor in self.contributors:
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

        repo_url = f"https://github.com/{self.arguments[0]}.git"

        if repo_url in CACHE:
            temp_dir = CACHE[repo_url]
        else:
            temp_dir = mkdtemp()
            # Clone repo
            try:
                Repo.clone_from(repo_url, temp_dir, multi_options=["--depth 1"])
            except Exception as e:
                del_directory_exists(temp_dir)
                raise ExtensionError("Invalid git repository given!", e)
            CACHE[repo_url] = temp_dir

        top_contributors = get_top_translators(temp_dir, locale).most_common(limit)

        if "alphabetical" in order:
            top_contributors.sort(key=lambda tup: strip_accents(tup[0]))

        return [
            ContributorSource(
                [
                    Contributor(name, hide_contributions, contributions)
                    for name, contributions in top_contributors
                ]
            ).build()
        ]

def cleanup_tempdirs(*args, **kwargs):
    for url, temp_dir in CACHE.items():
        del_directory_exists(temp_dir)
    CACHE.clear()


def setup(app: Sphinx) -> Dict[str, Any]:
    directives.register_directive("toptranslators", TopTranslators)
    app.connect("build-finished", cleanup_tempdirs)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": False,
    }
