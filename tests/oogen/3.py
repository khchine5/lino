# coding: latin1
# Luc Saffre 20041208

"""
oogen.elements
"""
import unittest
from cStringIO import StringIO

from lino.oogen.elements import H,P

class Case(unittest.TestCase):
	
	def test01(self):
		""
		e = P("This is a paragraph")
		s = StringIO()
		e.__xml__(s.write)
		self.assertEqual(s.getvalue(),"""\
<text:p text:style-name="Default">This is a paragraph</text:p>""")
		
		e = H(1,"This is a header")
		s = StringIO()
		e.__xml__(s.write)
		self.assertEqual(s.getvalue(),"""\
<text:h text:style-name="Heading 1" text:level=1>This is a header</text:h>""")

if __name__ == '__main__':
	unittest.main()

