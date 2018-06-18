# -*- coding: UTF-8 -*-
# Copyright 2012-2017 Luc Saffre
# License: BSD (see file COPYING for details)


from __future__ import unicode_literals
from builtins import str

from lino.core import constants as ext_requests
# from lino.core.renderer import HtmlRenderer, JsRenderer
from lino.core.renderer import add_user_language
from lino.core.menus import Menu, MenuItem
from lino.core import constants
from lino.modlib.extjs.ext_renderer import ExtRenderer

from lino.core.actions import (ShowEmptyTable, ShowDetail,
                               ShowInsert, ShowTable, SubmitDetail,
                               SubmitInsert)
from etgen.html import E

from .views import index_response

from lino.utils.jsgen import py2js


class Renderer(ExtRenderer):

    """.
        An HTML renderer that uses the OpenUI5 Javascript framework.

    """
    tableattrs = {'class': "table table-hover table-striped table-condensed"}
    cellattrs = dict(align="left", valign="top")

    can_auth = False

    # working, but shouldn't be used, as it clears the app history
    def get_detail_url(self, actor, pk, *args, **kw):
        """Opens detail however clears the app's history"""
        return self.plugin.build_plain_url(
            "#",
            "detail",
            actor.actor_id,
            str(pk), *args, **kw)

    def get_request_url(self, ar, *args, **kw):
        """Used for turn requests into urls"""
        if ar.actor.__name__ == "Main":
            return self.plugin.build_plain_url(*args, **kw)

        st = ar.get_status()
        kw.update(st['base_params'])
        add_user_language(kw, ar)
        if ar.offset is not None:
            kw.setdefault(ext_requests.URL_PARAM_START, ar.offset)
        if ar.limit is not None:
            kw.setdefault(ext_requests.URL_PARAM_LIMIT, ar.limit)
        if ar.order_by is not None:
            sc = ar.order_by[0]
            if sc.startswith('-'):
                sc = sc[1:]
                kw.setdefault(ext_requests.URL_PARAM_SORTDIR, 'DESC')
            kw.setdefault(ext_requests.URL_PARAM_SORT, sc)
        #~ print '20120901 TODO get_request_url

        return self.plugin.build_plain_url(
            ar.actor.app_label, ar.actor.__name__, *args, **kw)


    # # todo: port to ui5
    # def ar2js(self, ar, obj, **status):
    #     """Implements :meth:`lino.core.renderer.HtmlRenderer.ar2js`.
    #
    #     """
    #     rp = ar.requesting_panel
    #     ba = ar.bound_action
    #
    #     if ba.action.is_window_action():
    #         # Window actions have been generated by
    #         # js_render_window_action(), so we just call its `run(`)
    #         # method:
    #         status.update(self.get_action_status(ar, ba, obj))
    #         return "Lino.%s.run(%s,%s)" % (
    #             ba.full_name(), py2js(rp), py2js(status))
    #
    #     # It's a custom ajax action generated by
    #     # js_render_custom_action().
    #
    #     # 20140429 `ar` is now None, see :ref:`welfare.tested.integ`
    #     params = self.get_action_params(ar, ba, obj)
    #     return "Lino.%s(%s,%s,%s,%s)" % (
    #         ba.full_name(), py2js(rp),
    #         py2js(ar.is_on_main_actor), py2js(obj.pk), py2js(params))
    #     # bound_action.a)

    def action_call(self, request, bound_action, status):

        a = bound_action.action
        if a.opens_a_window or (a.parameters and not a.no_params_window):
            fullname = ".".join(bound_action.full_name().rsplit(".",1)[::-1]) # moves action name to first arg,
            if request and request.subst_user:
                status[
                    constants.URL_PARAM_SUBST_USER] = request.subst_user
            if isinstance(a, ShowEmptyTable):
                status.update(record_id=-99998)
            if request is None:
                rp = None
            else:
                rp = request.requesting_panel
            if not status:
                status = {} #non param window actions also use router and just have no args,

            return "me.open_window_action(%s,%s,%s)" % (
                py2js(fullname),
                py2js(status),
                py2js(rp))
        # todo: have action buttons forward their requests to the server with this js link
        return "%s()" % self.get_panel_btn_handler(bound_action)

    def show_menu(self, ar, mnu, level=1):
        """
        Render the given menu as an HTML element.
        Used for writing test cases.
        """
        if not isinstance(mnu, Menu):
            assert isinstance(mnu, MenuItem)
            if mnu.bound_action:
                sar = mnu.bound_action.actor.request(
                    action=mnu.bound_action,
                    user=ar.user, subst_user=ar.subst_user,
                    requesting_panel=ar.requesting_panel,
                    renderer=self, **mnu.params)
                # print("20170113", sar)
                url = sar.get_request_url()
            else:
                url = mnu.href
            assert mnu.label is not None
            if url is None:
                return E.p()  # spacer
            return E.li(E.a(mnu.label, href=url, tabindex="-1"))

        items = [self.show_menu(ar, mi, level + 1) for mi in mnu.items]
        #~ print 20120901, items
        if level == 1:
            return E.ul(*items, **{'class':'nav navbar-nav'})
        if mnu.label is None:
            raise Exception("%s has no label" % mnu)
        if level == 2:
            cl = 'dropdown'
            menu_title = E.a(
                str(mnu.label), E.b(' ', **{'class':"caret"}), href="#",
                data_toggle="dropdown", **{'class':'dropdown-toggle'})
        elif level == 3:
            menu_title = E.a(str(mnu.label), href="#")
            cl = 'dropdown-submenu'
        else:
            raise Exception("Menu with more than three levels")
        return E.li(
            menu_title,
            E.ul(*items, **{'class':'dropdown-menu'}),
            **{'class':cl})
