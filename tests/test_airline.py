import sys
sys.path.append("./crewScheduling")

from airline import Airline

new_company=None


def setup_module(module):
    global new_company

    new_company = Airline('data\\RoyalAirMaroc.cfg')


def test_loadFleet():
    new_company.loadFleet('data\\fleet.yml')
    
    assert new_company.aircrafts['B744']['range'] == 7260
