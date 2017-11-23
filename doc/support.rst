Support
=======

If you have problems or question with this project, there are several
options at your disposal:

.. no mailing list: * Write to the mailing list

* Try to troubleshoot the issue yourself
* Chat on IRC
* File bug reports

We of course welcome other contributions like documentation,
translations and patches, see the :doc:`contribute` guide for more
information on how to contribute to the project.

Troubleshooting
---------------

The basic way to troubleshoot this program is to run the same command as
you did when you had an error with the ``--verbose`` or, if that
doesn't yield satisfactory results, with the ``--debug`` output.

.. note:: The debug output outputs a lot of information and may be
          confusing for new users.

If you suspect there is a bug specific to your environment, you can
also try to see if it is reproducible within the
:ref:`testsuite`. From there, you can either file a bug report or try
to fix the issue yourself, see the :doc:`contribute` section for
more information.

Otherwise, see below for more options to get support.

.. Mailing list
.. ------------
..
.. No mailing list, if you have a mailing list, take example on the
.. monkeysign instructions:
.. https://monkeysign.readthedocs.io/en/2.x/support.html#mailing-list

Chat
----

We are often present in realtime in the ``#feed2exec`` channel of
the `Freenode network <https://freenode.net/>`_. You can join the channel
using `this link <ircs://irc.oftc.net/monkeysphere>`_ or `this web
interface
<https://webchat.freenode.net/?nick=feed2exec.&channels=feed2exec&prompt=1>`_.

.. raw:: html

         <iframe src="https://webchat.freenode.net/?nick=feed2exec.&channels=feed2exec&prompt=1" width="647" height="400"></iframe>

Bug reports
-----------

We want you to report bugs you find in this project. It's an important
part of contributing to a project, and all bug reports will be read and
replied to politely and professionally.

We are using an `issue tracker <issues>`_ to manage issues, and this
is where bug reports should be sent.

 .. _issues: https://gitlab.com/anarcat/feed2exec/issues

.. tip:: A few tips on how to make good bug reports:

         * Before you report a new bug, review the existing issues in
           the `online issue tracker`_ to make sure the bug has not
           already been reported elsewhere.

         * The first aim of a bug report is to tell the developers
           exactly how to reproduce the failure, so try to reproduce
           the issue yourself and describe how you did that.

         * If that is not possible, just try to describe what went wrong in
           detail. Write down the error messages, especially if they
           have numbers.

         * Take the necessary time to write clearly and precisely. Say
           what you mean, and make sure it cannot be misinterpreted.

         * Include the output of ``--version`` and ``--debug`` in your
           bug reports.

         If you wish to read more about issues regarding communication
         in bug reports, you can read `How to Report Bugs
         Effectively`_ which takes about 30 minutes.

.. no issue template yet:

.. See the :doc:`issue template <issue_template>` for more details
   about what to include in bug reports.

.. _online issue tracker: https://0xacab.org/monkeysphere/monkeysign/issues
.. _How to Report Bugs Effectively: http://www.chiark.greenend.org.uk/~sgtatham/bugs.html
         
.. warning:: The output of the ``--debug`` may show information you
             may want to keep private. Do review the output before
             sending it in bug reports.

Commercial support
------------------

The project maintainers are available for commercial support for this
software. If you have a feature you want to see prioritized or have a
bug you absolutely need fixed, you can sponsor this
development. Special licensing requirements may also be negociated if
necessary. See :doc:`contact` for more information on how to reach the
maintainers.
