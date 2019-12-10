API documentation
=================

This is the API documentation of the program. It should explain how to
create new plugins and navigate the code.

Controller module
-----------------

.. why can't this be just the __doc__ of the renderer module (ie. the
   top of file docstring)? somehow it fails to show up then...

This is the core modules that processes all feeds and talks to the
storage. It's where most of the logic lies, althought the parsing is
still currently done inside the model. It dispatches the plugin logic
to the plugin module.

.. automodule:: feed2exec.controller
   :members:


Model
-----

The "model" keeps track of feeds and their items. It handles
configuration and cache storage.

.. automodule:: feed2exec.model
   :members:

Main entry point
----------------

The main entry point of the program is in the
:mod:`feed2exec.__main__` module. This is to make it possible to call
the program directly from the source code through the Python
interpreter with::

  python -m feed2exec

All this code is here rather than in ``__init__.py`` to avoid
requiring too many dependencies in the base module, which contains
useful metadata for ``setup.py``.

This uses the :mod:`~click` module to define the base command and
options.

.. automodule:: feed2exec.__main__
   :members:

Plugins
-------

.. automodule:: feed2exec.plugins
   :members:

.. note:: actual plugins are documented in the :doc:`plugins`
          document.

Utilities
---------

Those are various utilities reused in multiple modules that did not
fit anywhere else.

.. automodule:: feed2exec.utils
   :members:
