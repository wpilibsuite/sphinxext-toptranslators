from docutils.parsers.rst import directives
from docutils import nodes
from git import Repo
from pathlib import Path
from sphinx.util.docutils import SphinxDirective
import os, stat
import shutil


TEMP_DIR_NAME = "temp_toptranslators"
TRANSLATORS_MARKER_NAME = "# Translators:"
# TODO REPLACE THIS WITH SPHINX ARG
LANGUAGES = ['es', 'fr']


# Workaround due to git-python storing handles after program execution
def del_rw(action, name, exc):
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


# Delete directory if exists
def del_directory_exists(directory: str):
    dirpath = Path(TEMP_DIR_NAME)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath, onerror=del_rw)
    else:
        print("Directory does not exist!")


def grab_contributors(path: str):
    found = False
    translators = []
    start = '# '
    end = ' <'
    with open(path, encoding="utf8") as f:
        for line in f.readlines():
            if found:
                if start not in line and end not in line:
                    break
                else:
                    line = line[line.find(start)+len(start):line.rfind(end)]
                    if len(line) > 2:
                        translators.append(line)
            if TRANSLATORS_MARKER_NAME in line:
                found = True

    return translators
    

# Clones the repo to get top translators
# Requires that git is currently in path
def get_top_translators(locale_path: str, locale: str):
    contributors = {}
    LOCALE_DIR = Path(TEMP_DIR_NAME + "/" + locale_path + "/" + locale + "/")
    for root, subFolder, files in os.walk(LOCALE_DIR, onerror=ValueError("Invalid locale directory of locale option!")):
        for item in files:
            if item.endswith(".po"):
                path = os.path.join(root, item)
                for contributor in grab_contributors(path):
                    if contributor not in contributors:
                        contributors[contributor] = 1
                    else:
                        contributors[contributor] += 1

    contributors = {contributor: contributors[contributor] for contributor in sorted(contributors, key=contributors.get, reverse=True)}

    return contributors


def get_config(app):
    return app.get_config()


class Contributor:
    def __init__(self, name, alphabetical, contributions=0):
        self.name = name
        self.alphabetical = alphabetical
        self.contributions = contributions


    def build(self):
        node_contributor = nodes.paragraph()
        node_contributor += nodes.reference(text=self.name)

        if self.alphabetical != True:
            node_contributor += nodes.Text(' - ' + str(self.contributions) + ' ' +
                                                    ('contributions' if self.contributions != 1 else 'contribution'))
        

class ContributorSource:
    def __init__(self, contributors, limit=10):
        self.contributors = contributors
        self.limit = limit


    def build(self):
        node_list = nodes.bullet_list()
        i = 0
        for contributor in self.contributors:
            node_contributor = nodes.list_item()
            node_contributor += contributor.build()
            node_list += node_contributor

            if i == limit:
                break

        return node_list


class TopTranslators(SphinxDirective):
    has_content = True
    required_arguments = 2
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'limit': directives.positive_int,
        'locale': directives.unchanged_required
        'order': directives.unchanged,
    }

    def run(self):
        limit = self.options.get('limit', 10)
        order = self.options.get('order', 'alphabetical')
        locale = self.options.get('local')

        config = get_config()
        top_translators_git = config["top_translators_git"]
        top_translators_locale = config["top_translators_locale"]

        del_directory_exists(TEMP_DIR_NAME)

        # Clone repo if given as parameter
        if (url is not None):
            try:
                Repo.clone_from(top_translators_git, TEMP_DIR_NAME)
            except:
                raise ValueError("Invalid git repository given!")
        
        contributors = get_top_translators(top_translators_locale, locale)
        alphabetical = order in alphabetical

        contributors_output = []
        for contributor in contributors.keys():
            contributors_output.append(Contributor(contributor, alphabetical, contributions[contributor]))

        return [ContributorSource(contributors_output, limit=limit)]
            
        

def setup(app):
    app.add_config_value("top_translators_git", None)
    app.add_config_value("top_translators_locale")
    directives.register_directive('toptranslators', TopTranslators)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": False,
    }