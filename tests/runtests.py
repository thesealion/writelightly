import unittest
from writelightly.tests import calendar, scrlist, input, metadata

loader = unittest.defaultTestLoader
suite = unittest.TestSuite()
for module in (calendar, scrlist, input, metadata):
    suite.addTest(loader.loadTestsFromModule(module))
unittest.TextTestRunner().run(suite)
