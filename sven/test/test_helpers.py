from django.test import SimpleTestCase
from sven import helpers


class HelpersTest(SimpleTestCase):
  def test_generic_helpers(self):
  	self.assertEqual(len(helpers.palette()), 1)