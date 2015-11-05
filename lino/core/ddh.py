# -*- coding: UTF-8 -*-
# Copyright 2009-2015 Luc Saffre
# License: BSD (see file COPYING for details)
"""Defines the :class:`DisableDeleteHandler` class.
"""

from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.db import models

from .utils import full_model_name as fmn


class DisableDeleteHandler():
    """A helper object used to find out whether a known object can be
    deleted or not.

    Lino installs an instance of this on each model in an attribute
    `_lino_ddh` during kernel startup.

    .. attribute:: fklist

        A list of tuples `(model, fk)`, one item for each FK field in
        the application which points to this model.

    .. attribute:: model

        The owning model (i.e. ``m._lino_ddh.model is m`` is True for
        every model)

    """

    def __init__(self, model):
        self.model = model
        self.fklist = []

    def add_fk(self, model, fk):
        # called from kernel during startup. fk_model is None for
        # fields defined on a parent model.

        for m, fld in self.fklist:
            if model is m:
                # avoid duplicate entries caused by MTI children
                return
        self.fklist.append((model, fk))

        def f(a, b):
            return cmp(
                fmn(a[0])+'.'+a[1].name, fmn(b[0])+'.'+b[1].name)
        self.fklist.sort(f)

    def __str__(self):
        s = ','.join([m.__name__ + '.' + fk.name for m, fk in self.fklist])
        return "<DisableDeleteHandler(%s, %s)>" % (self.model, s)

    def disable_delete_on_object(self, obj, ignore_models=set()):
        """Return a veto message which explains why this object cannot be
        deleted.  Return `None` if there is no veto.

        If `ignore_model` (a set of model class objects) is specified,
        do not check for vetos on ForeignKey fields defined on one of
        these models.

        """
        #logger.info("20101104 called %s.disable_delete(%s)", obj, self)
        # print "20150831 disable_delete", obj, self
        for m, fk in self.fklist:
            if m in ignore_models:
                # print "20150831 skipping", m, fk
                continue
            # if m.__name__.endswith("Partner") and fk.name == 'partner':
            # print 20150831, m, fk
            if fk.name in m.allow_cascaded_delete:
                continue
            if fk.null and fk.rel.on_delete == models.SET_NULL:
                continue
            n = m.objects.filter(**{fk.name: obj}).count()
            if n:
                return obj.delete_veto_message(m, n)
        kernel = settings.SITE.kernel
        # print "20141208 generic related objects for %s:" % obj
        for gfk, fk_field, qs in kernel.get_generic_related(obj):
            if gfk.name in qs.model.allow_cascaded_delete:
                continue
            if fk_field.null:  # a nullable GFK is no reason to veto
                continue
            n = qs.count()
            # print "20141208 - %s %s %s" % (
            #     gfk.model, gfk.name, qs.query)
            if n:
                return obj.delete_veto_message(qs.model, n)
        return None
