# -*- coding: utf-8 -*-

import os
import sys
parent = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.abspath(parent))

import feed2exec as mod  # noqa

extensions = [
    'sphinx.ext.autodoc',      # parse API docs
    'sphinx.ext.coverage',     # check for documentation coverage
    'sphinx.ext.intersphinx',  # cross-references
    'sphinx.ext.todo',         # .. todo:: items
    'sphinx.ext.viewcode',     # show code samples
]

# sort API documentation by source, not alphabetically
autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = mod.__prog__
copyright = mod.__copyright__
author = mod.__author__

# The short X.Y version.
version = mod.__version__
# The full version, including alpha/beta/rc tags.
release = version

# default language
language = None

exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Options for HTML output ----------------------------------------------
html_theme = 'default'

# on_rtd is whether we are on readthedocs.org, this line of code
# grabbed from docs.readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# would prefer alabaster theme because it is visually lighter, but it
# doesn't support arbitrary source links:
# https://github.com/bitprophet/alabaster/issues/87
if not on_rtd:  # only import and set the theme if we're building docs locally
    try:
        import sphinx_rtd_theme
        html_theme = 'sphinx_rtd_theme'
        html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    except ImportError:  # nosec
        pass

# link to original source instead of embeded
html_context = {
    'source_url_prefix': "https://gitlab.com/anarcat/feed2exec/blob/HEAD/doc/",
    'source_suffix': '.rst',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, '%s.tex' % mod.__prog__,
     u'%s Documentation' % mod.__prog__,
     mod.__author__, 'manual'),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('usage', mod.__prog__, u'%s Documentation' % mod.__prog__,
     [author], 1)
]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, mod.__prog__, u'%s Documentation' % mod.__prog__,
     author, mod.__prog__, 'One line description of project.',
     'Miscellaneous'),
]

# -- Options for Epub output ----------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'click': ('http://click.pocoo.org/', None),
    'jinja': ('http://jinja.pocoo.org/docs/', None),
    'python': ('https://docs.python.org/3/', None),
}
