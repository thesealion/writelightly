import unittest
from writelightly.tests import calendar, tests, scrlist

loader = unittest.defaultTestLoader
suite = unittest.TestSuite()
for module in (calendar, tests, scrlist):
    suite.addTest(loader.loadTestsFromModule(module))
unittest.TextTestRunner().run(suite)
