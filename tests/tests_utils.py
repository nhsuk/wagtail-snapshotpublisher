"""
.. module:: tests.tests_utils
"""

from django.test import Client, TestCase

from wagtailsnapshotpublisher.utils import *


class UtilsFunctionsTests(TestCase):
    """ UtilsFunctionsTests """

    def setUp(self):
        self.test_d = {
            'test1': {
                'test2': [
                    {
                        'test3': 'Value1'
                    },
                    {
                        'test4': 'Value2'
                    },
                ]
            },
            'test5': 'Value3',
        }

    # def test_get_from_dict(self):
    #     """ test_get_from_dict """
    #     self.assertEqual(get_from_dict(self.test_d, ['test1', 'test2', 1, 'test4']), 'Value2')
    #     self.assertEqual(get_from_dict(self.test_d, ['test5']), 'Value3')

    #     try:
    #         self.assertEqual(get_from_dict(self.test_d, ['test6']), 'Value3')
    #         self.assertFail('''KeyError haven't been raise''')
    #     except KeyError:
    #         pass

    #     try:
    #         self.assertEqual(get_from_dict(self.test_d, ['test1', 'test2', 3]), 'Value3')
    #         self.assertFail('''IndexError haven't been raise''')
    #     except IndexError:
    #         pass

    # def test_del_in_dict(self):
    #     """ test_del_in_dict """
    #     self.assertEqual(get_from_dict(self.test_d, ['test1', 'test2', 1, 'test4']), 'Value2')
    #     del_in_dict(self.test_d, ['test1', 'test2', 1, 'test4'])
    #     try:
    #         self.assertEqual(get_from_dict(self.test_d, ['test1', 'test2', 1, 'test4']), 'Value2')
    #         self.assertFail('''KeyError haven't been raise''')
    #     except KeyError:
    #         pass

    #     self.assertEqual(get_from_dict(self.test_d, ['test5']), 'Value3')
    #     del_in_dict(self.test_d, ['test5'])
    #     try:
    #         self.assertEqual(get_from_dict(self.test_d, ['test5']), 'Value3')
    #         self.assertFail('''KeyError haven't been raise''')
    #     except KeyError:
    #         pass

    #     try:
    #         del_in_dict(self.test_d, ['test6'])
    #         self.assertFail('''KeyError haven't been raise''')
    #     except KeyError:
    #         pass

    #     try:
    #         del_in_dict(self.test_d, ['test1', 'test2', 3])
    #         self.assertFail('''IndexError haven't been raise''')
    #     except IndexError:
    #         pass

    # def test_set_in_dict(self):
    #     """ test_set_in_dict """
    #     self.assertEqual(get_from_dict(self.test_d, ['test1', 'test2', 1, 'test4']), 'Value2')
    #     set_in_dict(self.test_d, ['test1', 'test2', 1, 'test4'], 'Value4')
    #     self.assertEqual(get_from_dict(self.test_d, ['test1', 'test2', 1, 'test4']), 'Value4')

    #     self.assertEqual(get_from_dict(self.test_d, ['test5']), 'Value3')
    #     set_in_dict(self.test_d, ['test5'], {'test6': 'Value5'})
    #     self.assertEqual(get_from_dict(self.test_d, ['test5']), {'test6': 'Value5'})

    #     try:
    #         set_in_dict(self.test_d, ['test7', 'test8'], 'Value6')
    #         self.assertFail('''KeyError haven't been raise''')
    #     except KeyError:
    #         pass

    #     try:
    #         set_in_dict(self.test_d, ['test1', 'test2', 3], 'Value7')
    #         self.assertFail('''IndexError haven't been raise''')
    #     except IndexError:
    #         pass
