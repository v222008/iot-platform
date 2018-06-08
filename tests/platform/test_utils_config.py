#!/usr/bin/env micropython
"""
SimpleConfig unittests
MIT license
(C) Konstantin Belyalov 2018
"""

import unittest
from platform.utils.config import SimpleConfig


# Tests

class ConfigTests(unittest.TestCase):

    def cb1(self):
        self.cb1_fired += 1

    def cb2(self):
        self.cb2_fired += 1

    def setUp(self):
        self.cb1_fired = 0
        self.cb2_fired = 0
        self.cfg = SimpleConfig(autosave=False)

    def testSanity(self):
        self.cfg.add_param('blah1', default=1)
        self.cfg.add_param('blah2', default='2')
        self.cfg.add_param('blah3', default=True)
        # Check default values
        self.assertEqual(self.cfg.blah1, 1)
        self.assertEqual(self.cfg.blah2, '2')
        self.assertEqual(self.cfg.blah3, True)
        # Update and check again
        self.cfg.update({'blah1': 11, 'blah2': '22', 'blah3': False})
        self.assertEqual(self.cfg.blah1, 11)
        self.assertEqual(self.cfg.blah2, '22')
        self.assertEqual(self.cfg.blah3, False)
        # There should be no callbacks
        self.assertEqual(self.cb1_fired, 0)
        self.assertEqual(self.cb2_fired, 0)
        # Add one more parameter with callback
        self.cfg.add_param('cb', default=100, callback=self.cb1)
        self.cfg.update({'cb': 200})
        # Ensure that only one parameter got changed
        self.assertEqual(self.cfg.blah1, 11)
        self.assertEqual(self.cfg.blah2, '22')
        self.assertEqual(self.cfg.blah3, False)
        self.assertEqual(self.cfg.cb, 200)
        # .. and callback was called
        self.assertEqual(self.cb1_fired, 1)
        # final check
        exp = {"blah2": "22", "cb": 200, "blah3": False, "blah1": 11}
        self.assertEqual(self.cfg.get_params(), exp)

    def testGroups(self):
        self.cfg.add_param('c1', default=1, callback=self.cb1)
        self.cfg.add_param('g1', default=2, callback=self.cb2, group=5)
        self.cfg.add_param('g2', default=3, group=5)
        # Update non group parameter, then check for callback fired
        self.cfg.update({'c1': 11})
        self.assertEqual(self.cb1_fired, 1)
        self.assertEqual(self.cb2_fired, 0)
        # Update two parameters in the same group
        self.cfg.update({'g1': 22, 'g2': 33})
        self.assertEqual(self.cb1_fired, 1)
        self.assertEqual(self.cb2_fired, 1)
        # Update one parameters in the same group
        self.cfg.update({'g2': 44})
        self.assertEqual(self.cb1_fired, 1)
        self.assertEqual(self.cb2_fired, 2)
        # Ensure that config has right values
        exp = {"c1": 11, "g1": 22, "g2": 44}
        self.assertEqual(self.cfg.get_params(), exp)

    def testValidators(self):
        def validator(name, value):
            if name != 'key1':
                raise KeyError()
            if value != 'value1':
                raise ValueError()
        # Default values validation
        # Validator as function
        self.cfg.add_param('key1', default='value1', validator=validator)
        # Invalid values
        with self.assertRaises(KeyError):
            self.cfg.add_param('key3', default='value3', validator=validator)
        with self.assertRaises(ValueError):
            self.cfg.update({'key1': 'blahinvalid'})


if __name__ == '__main__':
    unittest.main()
