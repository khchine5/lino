# -*- coding: UTF-8 -*-
# Copyright 2009-2016 by Luc Saffre.
# License: BSD, see LICENSE for more details.

"""Date formatting functions
-------------------------

To run the Lino test suite on this module::

  $ python setup.py test -s tests.UtilsTests.test_format_date

This module provides shortcuts to `python-babel`'s `date formatting
functions <http://babel.pocoo.org/docs/dates/>`_.

Note that if you ask just for English, then we change Babel's default
localization (US) to UK because US date format is just silly for
non-americans (no further comment).

>>> from lino import startup
>>> startup()
>>> import datetime
>>> d = datetime.date(2013, 8, 26)
>>> print(fds(d)) # short
26/08/2013
>>> print(fdm(d)) # medium
26 Aug 2013
>>> print(fdl(d)) # long
26 August 2013
>>> print(fdf(d)) # full
Monday, 26 August 2013
>>> print(fdmy(d)) # full
August 2013


The :func:`lino.core.format_date.format_date` function is a thin
wrapper to the corresponding function in `babel.dates`, filling the
`locale` parameter according to Django's current language (and doing
the conversion).

The major advantage over using `date_format` from
`django.utils.formats` is that Babel offers a "full" format:

>>> today = datetime.date(2013,1,18)

>>> print(format_date(today,'full'))
Friday, 18 January 2013

>>> with translation.override('fr'):
...    print(format_date(today,'full'))
vendredi 18 janvier 2013

>>> with translation.override('de'):
...    print(format_date(today,'full'))
Freitag, 18. Januar 2013

You can use this also for languages that aren't on your site:

>>> with translation.override('et'):
...    print(format_date(today,'full'))
reede, 18. jaanuar 2013

>>> with translation.override('nl'):
...    print(format_date(today,'full'))
vrijdag 18 januari 2013


>>> with translation.override('de'):
...    print(fds(today))
18.01.13
>>> with translation.override('fr'):
...    print(fds(today))
18/01/2013
>>> with translation.override('en_US'):
...    print(fds(today))
1/18/13
>>> with translation.override('en'):
...    print(fds(today))
18/01/2013
>>> with translation.override('en_UK'):
...    print(fds(today))
18/01/2013


>>> print(fds('')) # empty string is tolerated
<BLANKLINE>
>>> print(fds('2014-10-12')) # not tolerated
Traceback (most recent call last):
  ...
Exception: Not a date: u'2014-10-12'

"""

from __future__ import unicode_literals, print_function

import logging
logger = logging.getLogger(__name__)

import datetime
from babel.dates import format_date as babel_format_date

from django.conf import settings
from django.utils import translation
from django.template import defaultfilters

from lino.core.site import to_locale
from lino.utils import IncompleteDate


def monthname(n):
    """
    Return the monthname for month # n in current language.
    """
    d = datetime.date(2013, n, 1)
    return defaultfilters.date(d, 'F')


def fdmy(d):
    """
    "format date as month and year" :
    return the specified date as a localized string of type 'June 2011'."""
    if d is None:
        return ''
    return defaultfilters.date(d, 'F Y')


def format_date(d, format='medium'):
    """Return the given date `d` formatted with `Babel's date formatting
    <http://babel.edgewall.org/wiki/Documentation/dates.html>`_ and
    using Django's current language.

    """
    if not d:
        return ''
    if isinstance(d, IncompleteDate):
        d = d.as_date()
    if not isinstance(d, datetime.date):
        raise Exception("Not a date: {0!r}".format(d))
    lng = translation.get_language()
    if lng is None:  # occured during syncdb
        lng = settings.SITE.languages[0].django_code
    loc = to_locale(lng)
    if loc == 'en':
        loc = 'en_UK'  # I hate US date format
    logger.info("20160525 format_date %s (loc=%s)", d, loc)
    return babel_format_date(d, format=format, locale=loc)


def fdf(d):
    return format_date(d, format='full')


def fdl(d):
    return format_date(d, format='long')


def fdm(d):
    return format_date(d, format='medium')


def fds(d):
    return format_date(d, format='short')


# backwards compatibility:
dtosl = fdf
dtosm = fdm
dtos = fds
dtomy = fdmy  # backward compat


def day_and_month(d):
    return format_date(d, "dd. MMMM")


