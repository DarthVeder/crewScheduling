import logging.config
import logging
import argparse
from crew_scheduling.airline import Airline
from crew_scheduling.pilot import Pilot
from datetime import datetime, timedelta

MAJOR = 4
MINOR = 0
PATCH = 0
VERSION = '.'.join(
    [str(x) for x in [MAJOR, MINOR, PATCH]]
)

LOGGING_DICT = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s], %(asctime)s, %(module)s, %(name)s, %(message)s'  # noqa: E501
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'level': logging.DEBUG,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'level': logging.DEBUG,
            'maxBytes': 1000000,
            'filename': 'crew_scheduler.log'
        }
    },
    'loggers': {
        'crew_scheduler': {
            'level': logging.DEBUG,
            'handlers': ['console_handler', 'file_handler'],
            'propagate': '0'
        }
    }
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='crew scheduler'
    )
    parser.add_argument(
        '--pilot',
        '-p',
        help='pilot configuration file',
        dest='pilot_file',
        required=True
    )
    parser.add_argument(
        '--log-level',
        dest='log_level',
        choices=['info', 'debug'],
        default='info'
    )
    parser.add_argument(
        '--log-dir',
        dest='log_dir',
        default=r'C:\home\FSXTools\crewScheduling\crew_scheduling'
    )
    parser.add_argument(
        '--start-date',
        '-s',
        help='start date, format "YYY-mm-dd"',
        dest='start_date',
        type=lambda d: datetime.strptime(d, '%Y-%m-%d'),
        required=True
    )
    parser.add_argument(
        '--hub',
        help='hub',
        dest='hub',
        required=False
    )

    args = parser.parse_args()
    try:
        if args.log_level == 'debug':
            LOGGING_DICT['handlers']['console_handler']['level'] = logging.DEBUG
            LOGGING_DICT['handlers']['file_handler']['level'] = logging.DEBUG
        elif args.log_level == 'info':
            LOGGING_DICT['handlers']['console_handler']['level'] = logging.INFO
            LOGGING_DICT['handlers']['file_handler']['level'] = logging.INFO
    except Exception as e:
        print(e)
        exit(1)

    logging.config.dictConfig(LOGGING_DICT)
    logger = logging.getLogger('crew_scheduler')

    logger.info('starting')
    logger.debug('args: {}'.format(args))

    try:
        logger.info(
            'loading pilot file {}'
            .format(args.pilot_file)
        )
        pilot = Pilot(args.pilot_file)
        pilot.view_data()
    except Exception as e:
        logger.error(
            'Problems in loading pilot file. err={}'
            .format(e)
        )
        exit(1)

    logger.info(
        'loading company file {}'
        .format(pilot.get('company_file'))
    )
    logger.info(
        'pilot hub: '
        .format(pilot.get('hub'))
    )
    company = Airline(
        pilot.get('hub'), pilot.get('company_file')
    )

    old_aircraft_id = pilot.get('aircraft_id')
    pilot = company.assign_aircraft(pilot)
    company.assign_grade(pilot)
    if pilot.get('aircraft_id') != old_aircraft_id:
        logger.info(
            'Congratulations! You have been assigned to aircraft {}'
            .format(pilot.get('aircraft_id'))
        )
    schedule = company.assign_roster(pilot, args.start_date)
    logger.info(
        '{}'
        .format(schedule)
    )


    file_out = 'schedule_{}_{}.txt'\
        .format(
         pilot.get('name'), args.start_date.strftime('%d_%m_%y')
    )
    logger.info(
        'writing schedule file "{}"'.format(file_out)
    )
    company.format_schedule(schedule, file_out)
    pilot.set_last_airport(schedule.get('last_airport'))
    pilot.save_status()