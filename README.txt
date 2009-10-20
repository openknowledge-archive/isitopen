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

This material is open and licensed under the MIT license as follows:

Copyright (c) 2006-2009 Open Knowledge Foundation.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
