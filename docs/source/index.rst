.. Phoenix documentation master file, created by
   sphinx-quickstart on Wed Mar 11 13:38:39 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _introduction:

Introduction
============

Fawkes (the bird)
  *Fawkes is the NAME of a Phoenix, a long-lived bird that is cyclically regenerated or reborn.* (`Wikipedia <https://en.wikipedia.org/wiki/Phoenix_%28mythology%29>`_). [..]

Fawkes is a version of the Pyramid Phoenix web-application build with the Python web-framework :term:`birdhouse:pyramid`.
Fawkes has a user interface to make it easier to interact with the NAME :term:`Web Processing Services <birdhouse:wps>`.
For registered WPS services you can see which :ref:`processes` they have available.
You are provided with a form page to enter the parameters to :ref:`execute a process (job) <execute>`.
You can :ref:`monitor the jobs <myjobs>` and see the results.

Fawkes should help scientists run the Met Office model NAME, by controlling the WPS service :ref:`namewps`. Users can list
the available processes, and then run these processes by simply filling in the required information.

Fawkes has been adapted from the original Phoenix that has a more generic and technical user interface.
As Fawkes will only be running a single WPS, which known processes many of the more generic and technical interfaces have
been removed.

Fawkes is easy to install using the :term:`birdhouse:anaconda` python distribution and :term:`birdhouse:buildout`.
So, Fawkes is not only available on production sites where it is close to data archives.
You can also install it on your developer machine to make testing of your developed NAME-WPS processes easier and
to present them to other people.

.. toctree::
   :maxdepth: 2

   installation
   configuration
   user_guide
   tutorial
   troubleshooting

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

