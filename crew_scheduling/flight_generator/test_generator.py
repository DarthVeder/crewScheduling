import unittest
from generator import purge_other_hubs_connections


p_network_ok = {
    'LIPE': ['KJFK', 'LIRF', 'LIML'],
    'LIML': ['LIPE'],
    'EGPT': ['LIPE', 'LEML'],
    'LIRF': ['LIPE']
}

class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.network = {
            'LIPE': ['KJFK', 'LIRF', 'LIML'],
            'LIML': ['LIPE', 'EGLL', 'LIRF', 'KLAX'],
            'EGPT': ['LIPE', 'LEML'],
            'LEML': ['LIRF'],
            'LIRF': ['LIPE', 'LIML', 'EGPT', 'LEML', 'KBOS', 'KJFK', 'LEML']
        }

    def test_purge(self):
        assigned_hub = 'LIPE'
        hubs = ['LIRF', 'LIML']
        p_network = purge_other_hubs_connections(assigned_hub, hubs, self.network)

        for k in p_network:
            self.assertIn(k, p_network_ok)
        for k in p_network_ok:
            self.assertIn(k, p_network)

        for k in p_network_ok:
            self.assertListEqual(p_network[k], p_network_ok[k])