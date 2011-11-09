import unittest
from writelightly.tests import calendar, scrlist, input

loader = unittest.defaultTestLoader
suite = unittest.TestSuite()
for module in (calendar, scrlist, input):
    suite.addTest(loader.loadTestsFromModule(module))
unittest.TextTestRunner().run(suite)
