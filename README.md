# sphinxext-toptranslators

Sphinx extension to grab top contributors from a PO directory that Sphinx generates.

# Installation

`` pip install sphinxext-toptranslators ``

## Usage


### Directive Configuration
Directive is `` .. toptranslators:: GITHUB_REPO_NAME``

with the following options:

- *:locale:* name of the locale, examples are (fr, es). Please note that this flag is **mandatory**

- *:limit:* limit the number of shown contributors

- *:order:* default is `alphabetical`, but can be set to `numerical`

- *:hide_contributions:* Whether or not to hide how many contributions each contributor as made. default is `false`

### Example

```
  .. toptranslators:: wpilibsuite/frc-docs-translations
    :locale: fr
    :limit: 10
    :order: alphabetical
    :hide_contributions: true
```
