import logging
import logging.config
import json
import argparse
import random

MAJOR = '1'
MINOR = '0'
PATCH = '0'
VERSION = '.'.join([MAJOR, MINOR, PATCH])

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
            'level': logging.INFO,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'level': logging.INFO,
            'maxBytes': 1000000,
            'filename': 'flight_generator.log'
        }
    },
    'loggers': {
        'flight_generator': {
            'level': logging.DEBUG,
            'handlers': ['console_handler', 'file_handler'],
            'propagate': 'no'
        }
    }
}

MAX_HUBS = 10
# MAX_FLIGHTS_IN_SCHEDULE = 5


def read_flightradar_data(file_in):
    with open(file_in, 'r') as fin:
        data = json.load(fin)

    return data


def find_probable_hubs(network):
    conn = {}
    for apt in network:
        if len(network[apt]) > 1:
            conn[apt] = len(network[apt])
    probable_hubs = {
        k: v for k, v in sorted(
            conn.items(), key=lambda x: x[1], reverse=True
        )
    }
    while len(probable_hubs) > MAX_HUBS:
        probable_hubs.popitem()

    return list(probable_hubs.keys())


# def generate_schedule(dep_apt, pilot_network, visited):
#     flights = []
#     apt = dep_apt
#     while len(flights) < MAX_FLIGHTS_IN_SCHEDULE:
#         lnetwork = pilot_network.get(apt)
#         arr = random.choice(lnetwork)
#         flights.append(
#             [apt, arr]
#         )
#         visited[apt] = visited.get(apt, 0) + 1
#         apt = arr
#
#     end_apt = apt
#
#     return flights, visited, end_apt


def build_network(data):
    network = {}
    for i in data:
        dep = i.get("airport1")['icao']
        arr = i.get("airport2")['icao']
        if dep not in network.keys():
            network[dep] = [arr]
        else:
            network[dep].append(arr)

    return network


def show_data(network):
    conn = {}
    for k, v in network.items():
        conn[k] = len(v)

    total_conn = sum(conn.values())
    header = 'Network data:'
    logger.info(
        '\n'.join([
            header, '\n'.join([
                '{}: {} ({:0.2f}%)'
                .format(k, v, v / total_conn * 100)
                for k, v in conn.items()
            ])
        ])
    )
    probable_hubs = find_probable_hubs(network)
    logger.info(
        'possible hubs: [' +
        ', '.join(probable_hubs)
        + ']'
    )

    for hub in probable_hubs:
        connections = network.get(hub, None)
        if connections:
            logger.debug('HUB: {}  Destinations ({}): {}'
                         .format(hub, len(connections), connections))


# def format_schedule(flights):
#     header = ['Flt. Nr.    Dep     Arr     STD(LT)             STA(LT)    Blk. Hrs.    Start      End  ',
#               '----------------------------------------------------------------------------------------']
#     #          AT752       GMMN    EGLL    2020-03-01 07:00    10:30      03:30        06:30
#     #          AT775       EGLL    GMMN    2020-03-01 11:25    15:00      06:00
#     #          REPOSITION TO GMME                                         08:30                   16:00
#     #          AT063       GMME    LIML    2020-03-02 10:45    14:45      04:00        14:00
#     line = []
#     for d, a in flights:
#         line.append(
#             '{dep}  {arr}'.format(dep=d, arr=a)
#         )
#
#     text = '\n'.join(header + line)
#
#     return text

def generate_timetable(network, hubs):
    # Even flights number out from hubs, odd into hubs
    # if hub -> hub win the odd
    random.seed()
    flight_number = 200
    flights = []
    for apt in network:
        dep = apt
        if dep in hubs:
            if flight_number%2 != 0:  # odd, mak even
                flight_number += 1
        for c in network[apt]:
            number_of_flights = random.randint(1,5)
            if c in hubs:
                if flight_number%2 == 0: # even, make odd
                    flight_number += 1
            for n in range(number_of_flights):
                etd = '{:02d}{:02d}'.format(
                    random.randrange(0, 24, 1),
                    random.randrange(0, 60, 5)
                )
                flight = ('AV{}'.format(flight_number), dep, c, etd)
                flights.append(flight)
                flight_number += 1

    return flights


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Building airline network from Flightradar24 json file.'
    )

    parser.add_argument(
        '--version',
        default='%(prog)s {}'.format(VERSION),
        action='version')
    parser.add_argument(
        '--stats',
        '-s',
        help='print on screen some network stats and exit',
        action='store_const',
        dest='stats',
        const=True
    )
    parser.add_argument(
        '--verbosity',
        help='verbosity level',
        dest='verbosity',
        choices=['info', 'debug', 'error'],
        default='info'
    )
    parser.add_argument(
        '--log-dir',
        dest='log_dir',
        default=r'C:\home\FSXTools\crewScheduling\crewScheduling\flight_generator'
    )
    parser.add_argument(
        '-i',
        dest='file_in',
        default=None,
        required=True,
        help='input json file from Flightradar24'
    )
    parser.add_argument(
        '-o',
        help='output ASCII schedule file',
        default=None,
        dest='file_out'
    )
    parser.add_argument(
        '-n',
        help='print network json file',
        default=None,
        dest='file_network_out'
    )
    # parser.add_argument(
    #     '--from',
    #     dest='from_date',
    #     default=None
    # )
    # parser.add_argument(
    #     '--to',
    #     dest='to_date',
    #     default=None
    # )

    args = parser.parse_args()

    try:
        if args.verbosity == 'debug':
            LOGGING_DICT['handlers']['console_handler']['level'] = \
                logging.DEBUG
        elif args.verbosity == 'error':
            LOGGING_DICT['handlers']['console_handler']['level'] = \
                logging.ERROR

        if args.log_dir:
            filename = LOGGING_DICT['handlers']['file_handler']['filename']
            LOGGING_DICT['handlers']['file_handler']['filename'] = \
                '{}\{}'.format(args.log_dir, filename)

        logging.config.dictConfig(LOGGING_DICT)
        logger = logging.getLogger('flight_generator')

    except Exception as e:
        print(e)
        exit(1)

    logger.info('staring building network')
    logger.debug('args: {}'.format(args))

    file_in = args.file_in
    try:
        logger.info('reading file "{}"'.format(file_in))
        data = read_flightradar_data(file_in)
    except Exception as e:
        logger.error(str(e))
        exit(1)

    network = build_network(data)

    if args.stats:
        logger.info('building network statistics')
        show_data(network)
        exit(0)

    if args.file_network_out:
        try:
            logger.info('writing network json file "{}'.
                        format(args.file_network_out))
            fout = open(args.file_network_out, 'w')
            json.dump(network, fout, indent=4)
            fout.close()
        except Exception as e:
            logger.error('error in writing json network file "{}". {}'
                         .format(args.file_network_out, str(e)))
    # import random

    # random.seed()
    # hubs = ['SKBO', 'MSLP', 'SPJC', 'MROC', 'SEQM']
    hubs = None
    if not hubs:
        logger.info('no hub data. Guessing hubs')
        hubs = find_probable_hubs(network)
        logger.info('proposed hubs: {}'.format(' '.join(hubs)))

    assigned_hub = 'SPJC'
    flights = generate_timetable(network, hubs)
    logger.info(flights)

    # assigned_hub = None
    # if not assigned_hub:
    #     logger.info('assigning random hub')
    #     assigned_hub = random.choice(hubs)

    # if assigned_hub not in hubs:
    #     logger.error('assigned hub "{}" not in company hubs "{}'
    #                 .format(assigned_hub, ' '.join(hubs)))
    # logger.info('Assigned hub: {}'.format(assigned_hub))
    #
    # logger.info('computing assigned hub network')
    #
    # pilot_network = network.copy()
    # for hub in [h for h in hubs if h not in assigned_hub]:
    #     flights_to_remove = [x for x in pilot_network[hub]
    #                          if x not in assigned_hub]
    #     for f in flights_to_remove:
    #         pilot_network[hub].remove(f)
    #
    # logger.info('generating schedule')
    # if args.from_date is None:
    #     logger.error('need from date for generating a schedule')
    #     exit(1)
    #
    # pilot_visited = {}
    # apt = assigned_hub
    # for n in range(3):
    #     logger.debug('Schedule {}'.format(n+1))
    #     logger.debug('From {}'.format(apt))
    #     flights, pilot_visited, last_apt = \
    #         generate_schedule(apt, pilot_network, pilot_visited)
    #     apt = last_apt
    #
    #     schedule = format_schedule(flights)
    #     print(schedule)
    #     print()
    #
    # print(pilot_visited)
