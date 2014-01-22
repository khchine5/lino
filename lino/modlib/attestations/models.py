# -*- coding: UTF-8 -*-
# Copyright 2014 Luc Saffre
# This file is part of the Lino project.
# Lino is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# Lino is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Lino; if not, see <http://www.gnu.org/licenses/>.
"""
The :xfile:`models.py` file for :mod:`lino.modlib.attestations`.
"""

import logging
logger = logging.getLogger(__name__)

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from lino import dd
from lino import mixins
from django.conf import settings


outbox = dd.resolve_app('outbox')
postings = dd.resolve_app('postings')
contacts = dd.resolve_app('contacts')


class AttestationType(dd.BabelNamed, mixins.PrintableType,
                      outbox.MailableType):

    templates_group = 'attestations/Attestation'

    class Meta:
        verbose_name = _("Attestation Type")
        verbose_name_plural = _("Attestation Types")

    important = models.BooleanField(
        verbose_name=_("important"),
        default=False)
    remark = models.TextField(verbose_name=_("Remark"), blank=True)

    body_template = models.CharField(
        max_length=200,
        verbose_name=_("Body template"),
        blank=True, help_text="""The body template to be used when
rendering a printable of this type. This is a list of files
with extension `.body.html`.""")

    @dd.chooser(simple_values=True)
    def body_template_choices(cls):
        return settings.SITE.list_templates('.body.html',
                                            cls.get_templates_group())


class AttestationTypes(dd.Table):

    """
    Displays all rows of :class:`AttestationType`.
    """
    model = 'attestations.AttestationType'
    required = dd.required(user_level='admin', user_groups='office')
    column_names = 'name build_method template *'
    order_by = ["name"]

    insert_layout = """
    name
    build_method
    """

    detail_layout = """
    id name
    build_method template body_template email_template attach_to_email
    remark:60x5
    attestations.AttestationsByType
    """


class Attestation(mixins.TypedPrintable,
                  mixins.UserAuthored,
                  mixins.Controllable,
                  contacts.ContactRelated,
                  mixins.ProjectRelated,
                  outbox.Mailable,
                  postings.Postable,
              ):

    """
    Deserves more documentation.
    """

    manager_level_field = 'office_level'

    class Meta:
        abstract = settings.SITE.is_abstract_model('attestations.Attestation')
        verbose_name = _("Attestation")
        verbose_name_plural = _("Attestations")

    date = models.DateField(
        verbose_name=_('Date'), default=datetime.date.today)
    type = models.ForeignKey(AttestationType,
                             blank=True, null=True,
                             verbose_name=_('Attestation Type (Content)'))

    language = dd.LanguageField()

    def __unicode__(self):
        return u'%s #%s' % (self._meta.verbose_name, self.pk)

    def get_mailable_type(self):
        return self.type

    def get_print_language(self):
        return self.language

    def get_printable_context(self, ar, **kw):
        kw = super(Attestation, self).get_printable_context(ar, **kw)
        if self.type and self.type.body_template:
            tplname = self.type.body_template
            tplname = self.type.get_templates_group() + '/' + tplname
            saved_renderer = ar.renderer
            ar.renderer = settings.SITE.ui.plain_renderer
            template = settings.SITE.jinja_env.get_template(tplname)
            kw.update(body=template.render(**kw))
            ar.renderer = saved_renderer
        else:
            kw.update(body='')
        return kw


dd.update_field(Attestation, 'company',
                verbose_name=_("Recipient (Organization)"))
dd.update_field(Attestation, 'contact_person',
                verbose_name=_("Recipient (Person)"))


class AttestationDetail(dd.FormLayout):
    main = """
    date:10 type:25 project
    company contact_person contact_role
    id user:10 language:8 build_time
    outbox.MailsByController
    """


class Attestations(dd.Table):
    required = dd.required(user_groups='office', user_level='admin')

    model = 'attestations.Attestation'
    detail_layout = AttestationDetail()
    column_names = "id date user type project *"
    order_by = ["id"]


class MyAttestations(mixins.ByUser, Attestations):
    required = dd.required(user_groups='office')
    column_names = "date type project *"
    order_by = ["date"]


class AttestationsByType(Attestations):
    master_key = 'type'
    column_names = "date user *"
    order_by = ["date"]


class AttestationsByX(Attestations):
    required = dd.required(user_groups='office')
    column_names = "date type user *"
    order_by = ["-date"]

if settings.SITE.project_model is not None:

    class AttestationsByProject(AttestationsByX):
        master_key = 'project'


class AttestationsByOwner(AttestationsByX):
    master_key = 'owner'
    column_names = "date type user *"


class AttestationsByCompany(AttestationsByX):
    master_key = 'company'
    column_names = "date type user *"


class AttestationsByPerson(AttestationsByX):
    master_key = 'contact_person'
    column_names = "date type user *"


system = dd.resolve_app('system')


def setup_main_menu(site, ui, profile, m):
    m = m.add_menu("office", system.OFFICE_MODULE_LABEL)
    m.add_action('attestations.MyAttestations')


def setup_config_menu(site, ui, profile, m):
    m = m.add_menu("office", system.OFFICE_MODULE_LABEL)
    m.add_action('attestations.AttestationTypes')


def setup_explorer_menu(site, ui, profile, m):
    m = m.add_menu("office", system.OFFICE_MODULE_LABEL)
    m.add_action('attestations.Attestations')

