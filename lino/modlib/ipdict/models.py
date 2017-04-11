# -*- coding: UTF-8 -*-
# Copyright 2017 Luc Saffre
# License: BSD (see file COPYING for details)

"""The models module for this plugin.

"""
# from builtins import object
# from builtins import str

from django.conf import settings

# from django.db import models
from django.contrib.humanize.templatetags.humanize import naturaltime

from lino.api import dd, _

from lino.core.auth import get_auth_middleware

def format_timestamp(dt):
    if dt is None:
        return ''
    return u"{} {} ({})".format(
        dt.strftime(settings.SITE.date_format_strftime),
        dt.strftime(settings.SITE.time_format_strftime),
        naturaltime(dt))


class Connections(dd.VirtualTable):
    """

    """
    label = _("Connections")
    required_roles = dd.login_required(dd.SiteAdmin)
    column_names = "ip_address:12 login_failures:5 blacklisted_since:12 username:20 last_request:30 last_login:30"
    window_size = (90, 12)


    @classmethod
    def get_data_rows(cls, ar):
        auth = get_auth_middleware()
        return auth.ip_records.values()
    
    @dd.displayfield(_("IP address"))
    def ip_address(self, obj, ar):
        return obj.addr

    @dd.displayfield(_("Blacklisted since"))
    def blacklisted_since(self, obj, ar):
        return format_timestamp(obj.blacklisted_since)

    @dd.displayfield(_("Login failures"))
    def login_failures(self, obj, ar):
        return obj.login_failures

    @dd.displayfield(_("Username"))
    def username(self, obj, ar):
        return  obj.username

    @dd.displayfield(_("Last request"))
    def last_request(self, obj, ar):
        return format_timestamp(obj.last_request)

    @dd.displayfield(_("Last login"))
    def last_login(self, obj, ar):
        return format_timestamp(obj.last_login)

    
            