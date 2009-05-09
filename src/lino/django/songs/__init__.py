## Copyright 2009 Luc Saffre.
## This file is part of the Lino project. 

## Lino is free software; you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## Lino is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
## or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
## License for more details.

## You should have received a copy of the GNU General Public License
## along with Lino; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""
lino.django.songs

This is an experimental Django database to manage and/or 
document the activities of a choir.

"""
#
# menu setup
#
def lino_setup(lino):
    import models as reports
    m = lino.addMenu("songs","~Songs")
    m.addAction(reports.Rehearsals())
    m.addAction(reports.Singers())
    m.addAction(reports.Songs())
