# sphinxext-toptranslators

Sphinx extension to grab top contributors from a PO directory that Sphinx generates.

# Installation

`` pip install sphinxext-toptranslators ``

## Usage

### Global

*top_translators_locale_dir* - Value: (Str) Location of your locale directory

#### REQUIRED

*top_translators_git* - Value: (Str) URL of the github directory containing your locale

### Directive Configuration
Directive is `` .. toptranslators``

with the following options:
*:locale:* name of the locale, examples are (fr, es). Please note that this flag is **mandatory**
*:limit:* limit the number of shown contributors
*:order:* default is alphabetical, but can be set to numerical

### Example

```
  .. toptranslators::
    :locale: fr
    :limit: 10
```
