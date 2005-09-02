# coding: latin1
## Copyright 2003-2005 Luc Saffre

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
- loop through partners in Belgium, setting currency to EUR 
- test for equality of DataRow instances


"""
from lino.misc.tsttools import TestCase, main
from lino.apps.ledger import demo
from lino.apps.ledger.tables import Nation,Partner, Currency

class Case(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.sess = demo.startup() #dump=True)

    def tearDown(self):
        self.sess.shutdown()


    def test01(self):
        NATIONS = self.sess.query(Nation)
        CURR = self.sess.query(Currency)
        PARTNERS = self.sess.query(Partner)
        be = NATIONS.peek("be")
        BEF = CURR.peek('BEF')
        EUR = CURR.peek('EUR')
        q=PARTNERS.query("currency",
                         orderBy="name firstName",
                         nation=be)
        s = ""
        print self.getConsoleOutput()
        for p in q:
            #if p.currency is None:
            #   s += p.__str__() + " : currency remains None\n"
            if p.currency != EUR:
                # print p, p.currency.id
                s += p.__str__() + \
                     " : currency %s updated to EUR\n" % p.currency
                p.lock()
                p.currency = EUR
                p.unlock()
            else:
                s += str(p) + " : currency was already EUR\n"

        #print s
        self.assertEqual(s,"""\
Andreas Arens : currency BEF updated to EUR
Henri Bodard : currency BEF updated to EUR
Emil Eierschal : currency BEF updated to EUR
Erna Eierschal : currency BEF updated to EUR
Fr�d�ric Freitag : currency BEF updated to EUR
Gerd Gro�mann : currency BEF updated to EUR
PAC Systems PGmbH : currency BEF updated to EUR
""")
        
        


if __name__ == '__main__':
    main()

