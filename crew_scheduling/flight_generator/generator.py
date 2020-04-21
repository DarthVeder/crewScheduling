import logging
import logging.config
import json
import argparse
import random
from copy import deepcopy

MAJOR = '2'
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

MAX_HUBS = 4
MAX_FLIGHTS = 5
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
        'possible hubs: [{}]'
        .format(', '.join(probable_hubs))
    )

    for hub in probable_hubs:
        connections = network.get(hub, None)
        if connections:
            logger.debug('HUB: {}  Destinations ({}): {}'
                         .format(hub, len(connections), connections))


def generate_timetable(hub, network):
    # Even flights number out from assigned_hub hub, odd into assigned_hub
    # if assigned_hub -> hubs wins the odd
    flight_number = 200
    flights = []
    for apt in network:
        dep = apt
        if dep == hub:
            if flight_number%2 != 0:  # odd, mak even
                flight_number += 1
        for c in network[apt]:
            number_of_flights = random.randint(1,MAX_FLIGHTS)
            if c == hub:
                if flight_number%2 == 0: # even, make odd
                    flight_number += 1
            for n in range(number_of_flights):
                etd = '{:02d}{:02d}'.format(
                    random.randrange(0, 24, 1),
                    random.randrange(0, 60, 5)
                )
                flight = {
                    'number': '{}'.format(flight_number),
                    'dep': dep,
                    'arr': c,
                    'etd_lt': etd
                }
                flights.append(flight)
                flight_number += 1

    return flights


def purge_other_hubs_connections(assigned_hub, hubs, network):
    new_network = deepcopy(network)
    other_hubs = [h for h in hubs if h != assigned_hub]
    for hub in other_hubs:
        for d in [x for x in new_network[hub] if x != assigned_hub]:
            new_network[hub].remove(d)
            if hub in new_network.get(d, []):
                new_network[d].remove(hub)
                if len(new_network[d]) == 0:
                    del new_network[d]

    if len(new_network[hub]) == 0:
            del new_network[hub]

    return new_network


def make_gcmap_string(network):
    text = []
    for a, dests in network.items():
        for d in dests:
            text.append('-'.join([a, d]))

    return ','.join(text)


def export_fsc_format(assigned_hub, flights):
    header1 = '; {} generated flights with generator'\
        .format(len(flights))
    header2 = '; hub: {}'.format(assigned_hub)
    exported = [header1, header2]
    for f in flights:
        flight = 'Flight={flt},{dep},{arr},{size},{etd},0,,,,,'\
                 .format(flt=f['number'], dep=f['dep'], arr=f['arr'],
                         etd=f['etd_lt'], size=0)
        exported.append(flight)

    return '\n'.join(exported)


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
        default=r'C:\home\FSXTools\crewScheduling\crew_scheduling\flight_generator'
    )
    parser.add_argument(
        '--hub',
        dest='hub',
        default=None,
        help='hub for network'
    )
    parser.add_argument(
        '--hubs',
        dest='hubs',
        default=None,
        nargs='+',
        help='all company hubs'
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
                r'{}\{}'.format(args.log_dir, filename)

    except Exception as e:
        print(e)
        exit(1)

    random.seed()

    logging.config.dictConfig(LOGGING_DICT)
    logger = logging.getLogger('flight_generator')
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

    if args.hubs:
        hubs = args.hubs
        logger.info('hubs: {}'.format(' '.join(hubs)))
    else:
        hubs = find_probable_hubs(network)
        logger.info('proposed hubs (connections):')
        for h in hubs:
            logger.info('{} ({})'.format(h, len(network[h])))

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
            logger.error('error in writing json network file "{}". err={}'
                         .format(args.file_network_out, str(e)))

    if args.hub:
        assigned_hub = args.hub
        logger.info('assigned hub {}'.format(assigned_hub))
        logger.info('purging other hubs connections')
        network = purge_other_hubs_connections(assigned_hub, hubs, network)
    else:
        assigned_hub = None
        logger.info('computing flight for all network')

    logger.debug('gcmap: {}'.format(make_gcmap_string(network)))

    flights = generate_timetable(assigned_hub, network)
    logger.debug(flights)
    fout = open('tmp.txt', 'w')
    json.dump(network, fout, indent=4)
    fout.close()

    logger.info('exporting flights to "{}"'
                .format('crew_scheduling/flight_generator/schedule.txt'))
    schedule = export_fsc_format(assigned_hub, flights)
    fout = open('crew_scheduling/flight_generator/schedule.txt', 'w')
    fout.write(schedule)
    fout.close()

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
