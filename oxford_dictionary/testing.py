import unittest
from main import *

class testing(unittest.TestCase):

    def test_time_Oxford(self):
        online_test = OxfordDictionary()
        delta = time_func(online_test.search, "python")
        self.assertTrue(delta, delta[1]<1)

    def test_time_Local(self):
        local = LocalDictionary()
        delta = time_func(local.search, "foothill")
        self.assertTrue(delta, delta[1] < 1)

