Contribution guide
==================

This document outlines how to contribute to this project. It details
instructions on how to submit issues, bug reports and patches.

Before you participate in the community, you should agree to respect
the :doc:`code`.

.. include:: refs.rst.inc

Positive feedback
-----------------

Even if you have no changes, suggestions, documentation or bug reports
to submit, even just positive feedback like "it works" goes a long
way. It shows the project is being used and gives instant
gratification to contributors. So we welcome emails that tell us of
your positive experiences with the project or just thank you
notes. Head out to :ref:`contact` for contact informations or submit
a closed issue with your story.

You can also send your "thanks" through `saythanks.io
<https://saythanks.io/to/anarcat>`_.

.. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg 
   :alt: Say thanks to the author
   :target: https://saythanks.io/to/anarcat

Documentation
-------------

We love documentation!

The documentation resides in various `Sphinx
<http://www.sphinx-doc.org/>`_ documentations and in the README
file. Those can can be `edited online`_ once you register and changes
are welcome through the normal patch and merge request system.

Issues found in the documentation are also welcome, see below to file
issues in our tracker.

Issues and bug reports
----------------------

We want you to report issuess you find in the software. It is a
recognized and important part of contributing to this project. All
issues will be read and replied to politely and
professionnally. Issues and bug reports should be filed on the `issue
tracker <issues_>`_.

Issue triage
~~~~~~~~~~~~

Issue triage is a useful contribution as well. You can review the
`issues`_ in the `project page <project_>`_ and, for each issue:

-  try to reproduce the issue, if it is not reproducible, label it with
   ``more-info`` and explain the steps taken to reproduce
-  if information is missing, label it with ``more-info`` and request
   specific information
-  if the feature request is not within the scope of the project or
   should be refused for other reasons, use the ``wontfix`` label and
   close the issue
-  mark feature requests with the ``enhancement`` label, bugs with
   ``bug``, duplicates with ``duplicate`` and so on...

Note that some of those operations are available only to project
maintainers, see below for the different statuses.

Security issues
~~~~~~~~~~~~~~~

Security issues should first be disclosed privately to the project
maintainers (see :doc:`contact`), which support receiving encrypted
emails through the usual OpenPGP key discovery mechanisms.

This project cannot currently afford bounties for security issues. We
would still ask that you coordinate disclosure, giving the project a
reasonable delay to produce a fix and prepare a release before public
disclosure.

Public recognition will be given to reporters security issues if
desired. We otherwise agree with the `Disclosure Guidelines`_ of the
`HackerOne project`_, at the time of writing.

.. _Disclosure Guidelines: https://www.hackerone.com/disclosure-guidelines
.. _HackerOne project: https://www.hackerone.com/

Patches
-------

Patches can be submitted through `merge requests`_ on the `project
page <project_>`_.

Some guidelines for patches:

-  A patch should be a minimal and accurate answer to exactly one
   identified and agreed problem.
-  A patch must compile cleanly and pass project self-tests on all
   target platforms.
-  A patch commit message must consist of a single short (less than 50
   characters) line stating a summary of the change, followed by a blank
   line and then a description of the problem being solved and its
   solution, or a reason for the change. Write more information, not
   less, in the commit log.
-  Patches should be reviewed by at least one maintainer before being
   merged.

Project maintainers should merge their own patches only when they have
been approved by other maintainers, unless there is no response within a
reasonable timeframe (roughly one week) or there is an urgent change to
be done (e.g. security or data loss issue).

As an exception to this rule, this specific document cannot be changed
without the consensus of all administrators of the project.

    Note: Those guidelines were inspired by the `Collective Code
    Construct Contract`_. The document was found to be a little too
    complex and hard to read and wasn't adopted in its entirety. See
    this `discussion`_ for more information.

.. _Collective Code Construct Contract: https://rfc.zeromq.org/spec:42/C4/
.. _discussion: https://github.com/zeromq/rfc/issues?utf8=%E2%9C%93&q=author%3Aanarcat%20

Patch triage
~~~~~~~~~~~~

You can also review existing pull requests, by cloning the contributor's
repository and testing it. If the tests do not pass (either locally or
in the online Continuous Integration (CI) system), if the patch is
incomplete or otherwise does not respect the above guidelines, submit a
review with "changes requested" with reasoning.

Testing
-------

Running tests is strongly recommended before filing issues and
submitting patches. Patches that break tests will not be accepted. We
also aim to have complete test coverage, so you may be requested to
submit a test alongside new features or bugfixes. See the
:ref:`testsuite` section for more information.

Membership
----------

There are three levels of membership in the project, Administrator (also
known as "Owner" in GitHub or GitLab), Maintainer (also known as
"Member" on GitHub or "Developer" on GitLab), or regular users (everyone
with or without an account). Anyone is welcome to contribute to the
project within the guidelines outlined in this document, regardless of
their status, and that includes regular users.

Maintainers can:

-  do everything regular users can
-  review, push and merge pull requests
-  edit and close issues

Administrators can:

-  do everything maintainers can
-  add new maintainers
-  promote maintainers to administrators

Regular users can be promoted to maintainers if they contribute to the
project, either by participating in issues, documentation or pull
requests.

Maintainers can be promoted to administrators when they have given
significant contributions for a sustained timeframe, by consensus of the
current administrators. This process should be open and decided as any
other issue.

Release process
---------------

 .. _Semantic Versioning: http://semver.org/

To make a release:

1. make sure tests pass::

       tox

2. generate release notes with::

       gbp dch

3. tag the release according to `Semantic Versioning`_ rules::

       git tag -s x.y.z

4. build and test the Python package::

       python3 -m build
       sudo pip3 install dist/*.whl
       feed2exec --version
       sudo pip3 uninstall feed2exec

   .. note:: the `build` module might require an install.

5. build and test the debian package::

       gbp buildpackage
       sudo dpkg -i ../feed2exec_*.deb
       feed2exec --version
       sudo dpkg --remove feed2exec

6. push changes::

       git push
       twine upload dist/*
       dput ../feed2exec*.changes

7. edit the `tag`_ and copy-paste the changelog entry
