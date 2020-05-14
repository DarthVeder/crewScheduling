import logging
import unittest
from unittest import mock
from crew_scheduling.airline import Airline, load_fleet
import os


logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')


B747_range_ok = 7260

schedule_data = \
'''Flight=200,GMMN,KJFK,4,1228,0,,,,,
Flight=201,KJFK,GMMN,4,0039,0,,,,,
Flight=550,DXXX,GMMN,4,0314,0,,,,,
Flight=958,GMMN,LIPE,3,0913,0,,,,,
Flight=454,GMMN,GMFO,2,2353,0,,,,,
Flight=460,GMMZ,GMMN,2,0658,0,,,,,
Flight=492,GMMH,GMAD,2,2228,0,GMMN,,,,
'''


class TestLoadFleet(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.company = Airline(
            hub='GMMN',
            config_file=os.path.join('data', 'RoyalAirMaroc.cfg')
        )
        logging.disable(logging.NOTSET)

    def test_load_fleet(self):
        logging.disable(logging.CRITICAL)
        load_fleet(
            os.path.join('data', 'fleet.yml')
        )
        logging.disable(logging.NOTSET)

        self.assertEqual(self.company.aircrafts['B744']['range'], B747_range_ok)

    def test_build_route(self):
        with mock.patch('builtins.open', mock.mock_open(read_data=schedule_data)):
            flights = self.company._build_routes(file_schedule='foo')

        for f in flights:
            for a in flights[f].aircraft:
                self.assertGreaterEqual(self.company.get_aircraft_range(a), flights[f].distance)


if __name__ == '__main__':
    unittest.main()