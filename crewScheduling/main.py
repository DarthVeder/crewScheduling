'''
crew scheduler. It generates a fictitious scheduling.
Author: Marco Messina
Copyright: 2019 -
Licence: GNU 3.0
'''

import collections
import logging.config

MINIMUM_AIRCRAFT_PREPARATION_TIME_HRS = 1.0
MINIMUM_FLIGHT_TIME_DISTANCE_HRS = 5/60
FSX_DIRECTORY = './data/'
MAXIMUM_FLIGHT_TIME_HRS = 14.0

MAJOR = 1
MINOR = 0
PATCH = 0
VERSION = '.'.join(
    [str(x) for x in [MAJOR, MINOR, PATCH]]
)
MAX_HUBS = 10
MAX_FLIGHTS_IN_SCHEDULE = 5

logging_dict = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s'  # noqa: E501
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'scheduler': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': 'no'
        }
    }
}



if __name__ == '__main__':
    load = False
    if not load:
        company_config_file = 'RoyalAirMaroc.cfg'
        company_schedule_file = 'RoyalAirMaroc_schedule.txt'
        company_fleet_file = 'fleet.yml'

        new_company = Airline(company_config_file)

        pilot1 = Pilot('Giovannino Liguori')
        new_company.assignPilot(pilot1)
        pilot2 = Pilot('Ibrahim Mustafà')
        new_company.assignPilot(pilot2)

        new_company.loadFleet(company_fleet_file)
        new_company.buildRoutes(company_schedule_file)
        new_company.setActivePilot(pilot1)
        new_company.assignAircraftToActivePilot()
        new_company.assignGrade()

        # Saving to file
        new_company.pickle()
    else:
        # To recover from file:
        new_company = Airline()
        new_company = Airline.unpickle()

        # new_company.assignAircraftToPilot()
        # new_company.assignGrade()

    print('Active pilot: {}'.format(new_company.active_pilot.retrieve()))

    new_company.assignRoster()