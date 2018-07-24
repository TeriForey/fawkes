.. _tutorial_namerun:

Run NAME
==========================

Follow this tutorial to run NAME using all available user-defined options.
First you need to login. Please follow the login instructions in the :ref:`user guide <login>`.

.. contents::
   :local:
   :depth: 2
   :backlinks: none


Select NAME-WPS Process
----------------------

Go to the ``Processes`` tab.

.. image:: ../_images/tutorial/Processes.png

Click on *Run NAME-on-JASMIN* and you will get a form to enter the process parameters.

.. image:: ../_images/tutorial/namerun.png


Enter Process Parameters
------------------------

First enter a title for this run. Note, spaces will be converted to underscores.

.. image:: ../_images/tutorial/namerun_title.png

Then select the release location by entering the longitude in decimal degrees. This value cannot exceed +/-180.

.. image:: ../_images/tutorial/namerun_lon.png

Do the same for the latitude of release, in this case the value cannot exceed +/-90.

.. image:: ../_images/tutorial/namerun_lat.png

Enter the release elevation in meters.

.. image:: ../_images/tutorial/namerun_ele.png

Tick the checkbox if you wish to run NAME backwards from the time of release, or leave it to run NAME forwards.

.. image:: ../_images/tutorial/namerun_bck.png

Using the following two boxes select how long you want to run NAME over, in hours or days.
Note, the maximum permitted value is 20 days.

.. image:: ../_images/tutorial/namerun_time.png

Select the computational domain NAME will calculate the dispersion within. Enter the minimum
and maximum longitude (X) and latitude (Y) values.

.. image:: ../_images/tutorial/namerun_domain.png

Next, choose the output elevation ranges you which to calculate the particle dispersion within.
Multiple values can be added by continuing to click on the blue link. Note that values entered here must be two numbers
separated by a dash.

.. image:: ../_images/tutorial/namerun_outele.png

Use the dropdown box to select the resolution to run NAME within. The options are 0.05 or 0.25 degrees. Note that we don't
recommend using 0.05 degrees for runs longer than 5 days.

.. image:: ../_images/tutorial/namerun_resolution.png

Select how often you want the simulated particles released each day, either daily (i.e. once) or 3-hourly (8 times).

.. image:: ../_images/tutorial/namerun_type.png

If you selected daily above, you can then choose at what time you want the particles released and how long for.

.. image:: ../_images/tutorial/namerun_daily.png

Finally, enter the start and end dates that you'd like NAME to run within. Note, these are inclusive and as with all NAME
time parameters are considered within the Coordinated Universal Time (UTC) and not any local timezone.

.. image:: ../_images/tutorial/namerun_submit.png

After choosing all the above options, click ``submit`` to run this job on JASMIN.

Monitor running Job
-------------------

The job is now submitted and can be monitored on the *Monitor* page:

.. image:: ../_images/tutorial/Monitor.png

Click on the green refresh icon to check the status of the job.

Display the outputs
-------------------

Click on the details link to see a running log of the job process.

.. image:: ../_images/tutorial/fawkes_std_log.png

Click on the *Outputs* tab to show the run outputs - a job ID, zipped folder and an example plot.

.. image:: ../_images/tutorial/fawkes_std_outputs.png








