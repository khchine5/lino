# -*- coding: UTF-8 -*-
# Copyright 2009-2017 Luc Saffre
# License: BSD (see file COPYING for details)

"""Views for `lino.modlib.bootstrap3`.

"""
from __future__ import division
from past.utils import old_div

import logging
logger = logging.getLogger(__name__)

from django import http
from django.conf import settings
from django.views.generic import View
from django.core import exceptions
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
# from django.contrib import auth
from lino.core import auth


# from lino.api import dd
from lino.core import constants
# from lino.core import auth
from lino.core.requests import BaseRequest
from lino.core.tablerequest import TableRequest
import json

from lino.core.views import requested_actor, action_request
from lino.core.views import json_response, json_response_kw

from lino.core.views import action_request
from lino.core.utils import navinfo
from etgen.html import E
from etgen import html as xghtml

from lino.api import rt
import re

# Taken from lino.modlib.extjs.views
NOT_FOUND = "%s has no row with primary key %r"
def elem2rec_empty(ar, ah, elem, **rec):
    """
    Returns a dict of this record, designed for usage by an EmptyTable.
    """
    #~ rec.update(data=rh.store.row2dict(ar,elem))
    rec.update(data=elem._data)
    #~ rec = elem2rec1(ar,ah,elem)
    #~ rec.update(title=_("Insert into %s...") % ar.get_title())
    rec.update(title=ar.get_action_title())
    rec.update(id=-99998)
    #~ rec.update(id=elem.pk) or -99999)
    if ar.actor.parameters:
        rec.update(
            param_values=ar.actor.params_layout.params_store.pv2dict(
                ar, ar.param_values))
    return rec

class ApiList(View):
    pass

class ApiElement(View):
    pass

class Choices(View):
    pass

class Restful(View):

    """
    Used to collaborate with a restful Ext.data.Store.
    """

    def post(self, request, app_label=None, actor=None, pk=None):
        rpt = requested_actor(app_label, actor)
        ar = rpt.request(request=request)

        instance = ar.create_instance()
        # store uploaded files.
        # html forms cannot send files with PUT or GET, only with POST
        if ar.actor.handle_uploaded_files is not None:
            ar.actor.handle_uploaded_files(instance, request)

        data = request.POST.get('rows')
        data = json.loads(data)
        ar.form2obj_and_save(data, instance, True)

        # Ext.ensible needs list_fields, not detail_fields
        ar.set_response(
            rows=[ar.ah.store.row2dict(
                ar, instance, ar.ah.store.list_fields)])
        return json_response(ar.response)

    # def delete(self, request, app_label=None, actor=None, pk=None):
    #     rpt = requested_actor(app_label, actor)
    #     ar = rpt.request(request=request)
    #     ar.set_selected_pks(pk)
    #     return delete_element(ar, ar.selected_rows[0])

    def get(self, request, app_label=None, actor=None, pk=None):
        """
        Works, but is ugly to get list and detail
        """
        rpt = requested_actor(app_label, actor)


        action_name = request.GET.get(constants.URL_PARAM_ACTION_NAME,
                                      rpt.default_elem_action_name)
        fmt = request.GET.get(
            constants.URL_PARAM_FORMAT,constants.URL_FORMAT_JSON)
        sr = request.GET.getlist(constants.URL_PARAM_SELECTED)
        if not sr:
            sr = [pk]
        ar = rpt.request(request=request, selected_pks=sr)
        if pk is None:
            rh = ar.ah
            rows = [
                rh.store.row2dict(ar, row, rh.store.all_fields)
                for row in ar.sliced_data_iterator]
            kw = dict(count=ar.get_total_count(), rows=rows)
            kw.update(title=str(ar.get_title()))
            return json_response(kw)

        else: #action_name=="detail": #ba.action.opens_a_window:

            ba = rpt.get_url_action(action_name)
            ah = ar.ah
            ar = ba.request(request=request, selected_pks=sr)
            elem = ar.selected_rows[0]
            if fmt == constants.URL_FORMAT_JSON:
                if pk == '-99999':
                    elem = ar.create_instance()
                    datarec = ar.elem2rec_insert(ah, elem)
                elif pk == '-99998':
                    elem = ar.create_instance()
                    datarec = elem2rec_empty(ar, ah, elem)
                elif elem is None:
                    datarec = dict(
                        success=False, message=NOT_FOUND % (rpt, pk))
                else:
                    datarec = ar.elem2rec_detailed(elem)
                return json_response(datarec)


    def put(self, request, app_label=None, actor=None, pk=None):
        rpt = requested_actor(app_label, actor)
        ar = rpt.request(request=request)
        ar.set_selected_pks(pk)
        elem = ar.selected_rows[0]
        rh = ar.ah

        data = http.QueryDict(request.body).get('rows')
        data = json.loads(data)
        a = rpt.get_url_action(rpt.default_list_action_name)
        ar = rpt.request(request=request, action=a)
        ar.renderer = settings.SITE.kernel.extjs_renderer
        ar.form2obj_and_save(data, elem, False)
        # Ext.ensible needs list_fields, not detail_fields
        ar.set_response(
            rows=[rh.store.row2dict(ar, elem, rh.store.list_fields)])
        return json_response(ar.response)


def http_response(ar, tplname, context):
    "Deserves a docstring"
    u = ar.get_user()
    lang = get_language()
    k = (u.user_type, lang)
    context = ar.get_printable_context(**context)
    context['ar'] = ar
    context['memo'] = ar.parse_memo  # MEMO_PARSER.parse
    env = settings.SITE.plugins.jinja.renderer.jinja_env
    template = env.get_template(tplname)

    response = http.HttpResponse(
        template.render(**context),
        content_type='text/html;charset="utf-8"')

    return response


def XML_response(ar, tplname, context):
    """
    Respone used for rendering XML views in openui5.
    Includes some helper functions for rendering.
    """
    # u = ar.get_user()
    # lang = get_language()
    # k = (u.user_type, lang)
    context = ar.get_printable_context(**context)
    # context['ar'] = ar
    # context['memo'] = ar.parse_memo  # MEMO_PARSER.parse
    env = settings.SITE.plugins.jinja.renderer.jinja_env
    template = env.get_template(tplname)

    def bind(*args):
        """Helper function to wrap a string in {}s"""

        return "{" + "".join(args) + "}"

    context.update(bind=bind)

    def p(*args):
        """Debugger helper; prints out all args put into the filter but doesn't include them in the template.
        usage: {{debug | p}}
        """
        print(args)
        return ""

    env.filters.update(p=p)

    response = http.HttpResponse(
        template.render(**context),
        content_type='text/html;charset="utf-8"')

    return response


def layout2html(ar, elem):

    wl = ar.bound_action.get_window_layout()
    #~ print 20120901, wl.main
    lh = wl.get_layout_handle(settings.SITE.kernel.default_ui)

    items = list(lh.main.as_plain_html(ar, elem))
    # if navigator:
    #     items.insert(0, navigator)
    #~ print E.tostring(E.div())
    #~ if len(items) == 0: return ""
    return E.form(*items)


class Tickets(View):
    """
    Was a static View for Tickets,
    IS currently main app entry point,
    """
    def get(self, request, app_label="tickets", actor="AllTickets"):
        ar = action_request(app_label, actor, request, request.GET, True)
        ar.renderer = settings.SITE.plugins.openui5.renderer

        # ui = settings.SITE.plugins.openui5
        # main = settings.SITE.get_main_html(ar.request, extjs=ui)
        # main = ui.renderer.html_text(main)
        # print(main)
        context = dict(
            title=ar.get_title(),
            heading=ar.get_title(),
            # main=main,
        )

        context.update(ar=ar)

        context = ar.get_printable_context(**context)
        env = settings.SITE.plugins.jinja.renderer.jinja_env
        template = env.get_template("openui5/tickets_ui5.html")

        return http.HttpResponse(
            template.render(**context),
            content_type='text/html;charset="utf-8"')

class MainHtml(View):
    def get(self, request, *args, **kw):
        """Returns a json struct for the main user dashboard."""
        #~ logger.info("20130719 MainHtml")
        settings.SITE.startup()
        #~ raise Exception("20131023")
        ar = BaseRequest(request)
        html = settings.SITE.get_main_html(
            request, extjs=settings.SITE.plugins.openui5)
        html = settings.SITE.plugins.openui5.renderer.html_text(html)
        ar.success(html=html)
        return json_response(ar.response, ar.content_type)

class Connector(View):
    """
    Static View for Tickets,
    Uses a template for generating the XML views  rather then layouts
    """
    def get(self, request, name=None):
        # ar = action_request(None, None, request, request.GET, True)
        ar = BaseRequest(
            # user=user,
            request=request,
            renderer=settings.SITE.plugins.openui5.renderer)
        u = ar.get_user()

        context = dict(
            menu=settings.SITE.get_site_menu(None, u.user_type)
        )

        print(u)
        print name
        if name.startswith("view/"):
            tplname = "openui5/" + name

        elif name.startswith("dialog/SignInActionFormPanel"):
            tplname = "openui5/fragment/SignInActionFormPanel.fragment.xml"

        elif name.startswith("menu/user/user.fragment.xml"):
            tplname = "openui5/fragment/UserMenu.fragment.xml"

        elif name.startswith("menu/"):
            tplname = "openui5/fragment/Menu.fragment.xml"
            sel_menu = name.split("/",1)[1].split('.',1)[0]
            # [05/Feb/2018 09:32:25] "GET /ui/menu/mailbox.fragment.xml HTTP/1.1" 200 325
            for i in context['menu'].items:
                if i.name == sel_menu:
                    context.update(dict(
                        opened_menu=i
                    ))
                    break
            else:
                raise Exception("No Menu with name %s"%sel_menu)
        elif name.startswith("grid/") or name.startswith("slavetable/"): # Table/grid view
            # todo Get table data
            # "grid/tickets/AllTickets.view.xml"
            # or
            # "slavetable/tickets/AllTickets.view.xml"
            app_label, actor = re.match(r"(?:grid|slavetable)\/(.+)\/(.+).view.xml$", name).groups()
            actor = rt.models.resolve(app_label + "." + actor)
            context.update({
                "actor": actor,
                "columns": actor.get_handle().get_columns(),
                "actions": actor.get_actions(),
                "title": actor.label,

            })
            if name.startswith("slavetable/"):
                tplname = "openui5/view/slaveTable.view.xml"
            else:
                tplname = "openui5/view/table.view.xml" # Change to "grid" to match action?
            # ar = action_request(app_label, actor, request, request.GET, True)
            # add to context

        elif name.startswith("detail"):  # Detail view
            # "detail/tickets/AllTickets.view.xml"
            app_label, actor = re.match(r"detail\/(.+)\/(.+).view.xml$", name).groups()
            actor = rt.models.resolve(app_label + "." + actor)
            # detail_action = actor.actions['detail']
            detail_action = actor.detail_action
            window_layout = detail_action.get_window_layout()
            layout_handle = window_layout.get_layout_handle(settings.SITE.plugins.openui5)
            layout_handle.main.elements # elems # Refactor into actor get method?
            context.update({
                "actor": actor,
                # "columns": actor.get_handle().get_columns(),
                "actions": actor.get_actions(),
                "title": actor.label, #
                # "main_elems": layout_handle.main.elements,
                "main": layout_handle.main,
                "layout_handle": layout_handle

            })
            tplname = "openui5/view/detail.view.xml"  # Change to "grid" to match action?
            # ar = action_request(app_label, actor, request, request.GET, True)
            # add to context

        else:
            raise Exception("Can't find a view for path: {}".format(name))

        return XML_response(ar, tplname, context)



class Authenticate(View):
    def get(self, request, *args, **kw):
        action_name = request.GET.get(constants.URL_PARAM_ACTION_NAME)
        if action_name == 'logout':
            username = request.session.pop('username', None)
            auth.logout(request)
            # request.user = settings.SITE.user_model.get_anonymous_user()
            # request.session.pop('password', None)
            #~ username = request.session['username']
            #~ del request.session['password']
            target = '/'
            return http.HttpResponseRedirect(target)


            # ar = BaseRequest(request)
            # ar.success("User %r logged out." % username)
            # return ar.renderer.render_action_response(ar)
        raise http.Http404()

    def post(self, request, *args, **kw):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = auth.authenticate(
            request, username=username, password=password)
        auth.login(request, user, backend=u'lino.core.auth.backends.ModelBackend')
        target = '/'
        return http.HttpResponseRedirect(target)
        # ar = BaseRequest(request)
        # mw = auth.get_auth_middleware()
        # msg = mw.authenticate(username, password, request)
        # if msg:
        #     request.session.pop('username', None)
        #     ar.error(msg)
        # else:
        #     request.session['username'] = username
        #     # request.session['password'] = password
        #     # ar.user = request....
        #     ar.success(("Now logged in as %r" % username))
        #     # print "20150428 Now logged in as %r (%s)" % (username, user)
        # return ar.renderer.render_action_response(ar)

# Todo repalce with Tickets
class Index(View):
    """
    Render the main page.
    """
    def get(self, request, *args, **kw):
        # raise Exception("20171122 {} {}".format(
        #     get_language(), settings.MIDDLEWARE_CLASSES))
        ui = settings.SITE.plugins.bootstrap3
        # print("20170607", request.user)
        # assert ui.renderer is not None
        ar = BaseRequest(
            # user=user,
            request=request,
            renderer=ui.renderer)
        return index_response(ar)


def index_response(ar):
    ui = settings.SITE.plugins.openui5

    main = settings.SITE.get_main_html(ar.request, extjs=ui)
    main = ui.renderer.html_text(main)
    context = dict(
        title=settings.SITE.title,
        main=main,
    )
    # if settings.SITE.user_model is None:
    #     user = auth.AnonymousUser.instance()
    # else:
    #     user = request.subst_user or request.user
    # context.update(ar=ar)
    return http_response(ar, 'bootstrap3/index.html', context)
