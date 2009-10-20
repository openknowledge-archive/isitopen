This file is for you to describe the isitopen application.

Installation and Setup
======================

Make sure you are in the same directory as this file.

Install ``isitopen`` using easy_install::

    easy_install .

Make a config file as follows::

    paster make-config isitopen config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Then you are ready to go. Run the application with (for example):

		paster serve config.ini


Changelog
=========

v0.3 2009-10-??
---------------

  * Improve response and threading support (including notifications)
  * Admin interface

v0.2 2009-07-15
---------------

  * Email backend functional but quite raw
  * Significant development of domain model 
  * Rudimentary response and threading support

v0.1 2009-04-10
---------------

  * Basic webapp with enquiry and message creation (but no email backend)
  * Content for front page, about, guide


Contributors
============

  * Rufus Pollock <rufus [at] rufuspollock [dot] org>
  * Nick Stenning <nick [at] whiteink [dot] com>
  * Jenny Molloy
  * Peter Murray-Rust
  * Andrew Gruen

Copying
=======

The code is copyright (c) 2006-2009 Open Knowledge Foundation.

The code is open and licensed under the GNU Affero GPL v3.0:

    http://www.fsf.org/licensing/licenses/agpl-3.0.html

