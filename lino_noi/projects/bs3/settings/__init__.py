# -*- coding: UTF-8 -*-
# Copyright 2015 Luc Saffre
#
# This file is part of Lino Noi.
#
# Lino Noi is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lino Noi is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with Lino Noi.  If not, see
# <http://www.gnu.org/licenses/>.

"""Settings for providing readonly public access to the site. This
does not use :mod:`lino.modlib.extjs` but :mod:`lino.modlib.bootstrap3`.

"""

from lino_noi.projects.team.settings.demo import *


class Site(Site):

    default_ui = 'bootstrap3'
    default_user = 'anonymous'

    # def get_installed_apps(self):
    #     yield super(Site, self).get_installed_apps()
    #     yield 'lino.modlib.bootstrap3'

