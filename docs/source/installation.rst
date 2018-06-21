.. _installation:

Installation
============

This installation works on Linux 64-bit (Ubuntu 14.04, Centos 6, ...). It might still work on MacOSX but packages are updated only from time to time. Most of the dependencies come from :term:`birdhouse:Anaconda` Python distribution system. Additional conda packages come from the `Binstar channel Birdhouse <https://anaconda.org/birdhouse>`_. The installation is done with :term:`birdhouse:Buildout`.

Fawkes uses WPS processes provided by namewps. As a requisite you should install a local namewps WPS.

To install namewps follow the instructions given in the :ref:`NAME-WPS documentation <namewps:installation>`. In short:

.. code-block:: sh

   $ git clone https://github.com/TeriForey/namewps.git
   $ cd namewps
   $ make clean install

Now start with downloading Fawkes with sources from github:

.. code-block:: sh

   $ git clone https://github.com/TeriForey/fawkes.git
   $ cd fawkes

For install options run ``make help`` and read the documention for the :ref:`Makefile <bootstrap:makefile>`.

To change the anaconda location edit the ``Makefile.config``, for example::

   ANACONDA_HOME ?= /opt/anaconda
   CONDA_ENVS_DIR ?= /opt/anaconda/envs

Before installation you *need* to create a password for the local ``phoenix`` user which is used to login to the Fawkes web application:

.. code-block:: sh

   $ make passwd
   Generate Phoenix password ...
   Enter a password with at least 8 characters.
   Enter password:
   Verify password:

   Run 'make install restart' to activate this password.

Optionally take a look at ``custom.cfg`` and make additional changes. When you're finished, run ``make clean install`` to install Fawkes:

.. code-block:: sh

   $ make clean install

You always have to rerun ``make update`` after making changes in custom.cfg.

After successful installation you need to start the services. All installed files (config etc ...) are below the conda environment ``birdhouse`` which is by default in your home directory ``~/birdhouse``. Now, start the services:

.. code-block:: sh

   $ make start    # starts supervisor services
   $ make status   # shows status of supervisor services

Fawkes web application is available on `http://localhost:8081`.

Check the log file for errors:

.. code-block:: sh

   $ tail -f  ~/birdhouse/var/log/supervisor/phoenix.log
   $ tail -f  ~/birdhouse/var/log/supervisor/celery.log

Run Docker
----------

Set the ``HOSTNAME`` environment variable (not ``localhost``) and run ``docker-compose``:

.. code-block:: sh

   HOSTNAME=phoenix HTTP_PORT=8081 HTTPS_PORT=8443 SUPERVISOR_PORT=9001 docker-compose up
