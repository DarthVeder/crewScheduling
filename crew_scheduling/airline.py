# import pickle
import collections
import yaml
from datetime import datetime, timedelta, time
import logging
import random
import os
import configparser
from math import ceil
from crew_scheduling.point import Point, distance


logger = logging.getLogger('crew_scheduler.' + __name__)

Grade = collections.namedtuple('Grade', 'hours title')
Flight = collections.namedtuple('Flight', 'id dep arr time_lt distance aircraft')
Schedule = collections.namedtuple('Schedule', 'id dep arr dep_lt arr_lt block_time')

PRESENTATION_HRS = 45/60
AIRCRAFT_TURNOVER_HRS = 1.0
MINIMUM_FLIGHT_PERCENT_DISTANCE= 10
FSX_DIRECTORY = os.path.join('.', 'data', 'FSX')
MAXIMUM_FLIGHT_TIME_HRS = 10.0
MAXIMUM_BLOCK_HOURS = 14.0
MINIMUM_FLIGHTS_BEFORE_PROMOTION = 15
MAXIMUM_VISITED_DIFFERENCE = 5
# TODO
PROBABILITY_SPECIAL_MISSION = 15
SPECIAL_MISSIONS = [
    'retrieve new airplane',
    'reposition aircraft'
]

# def lmt2utc(latitude_deg, lmt):
#     deltat = timedelta(hours=latitude_deg/15.0)
#     utc = lmt - deltat
#
#     return utc
#
#
# def utc2lmt(latitude_deg, utc):
#     deltat = timedelta(hours=latitude_deg/15.0)
#     lmt = utc + deltat
#
#     return lmt


def load_fsx_data(file_fsx):
    # TODO: use runways.xml and add country information
    airports = {}
    with open(file_fsx, 'r') as fin:
        for line in fin:
            # Inserting only the first runway and its lat, lon. It is assumed
            # the airport has the same coordinates as the runway.
            (icao, hdg, lat, lon, *trash ) = line.split(',')
            if icao not in airports:
                airports[icao] = (float(lat), float(lon))

    return airports


def load_fleet(fleet_file):
    # Parsing Fleet file and saving the fleet in dictionary aircrafts.
    # Usage: aircrafts[id]['name' or 'ktas' or 'range']
    logger.info('loading fleet')
    with open(fleet_file, 'r') as file:
        aircrafts = yaml.full_load(file)
    progression = aircrafts.pop('progression')
    logger.debug('read {} aircrafts'.format(len(aircrafts)))
    for a, data in aircrafts.items():
        logger.debug(
            'aicraft {}, data {}'
            .format(a, data)
        )
    logger.info('aircraft progression: {}'.format(progression))
    logger.info('done')

    return progression, aircrafts


def nice_date(d):
    return d.strftime('%d/%m/%y')


def nice_datetime(d):
    return d.strftime('%d/%m/%y %H:%M')


def nice_time(d):
    return d.strftime('%H:%M')


def find_min_range_aircraft(aircrafts):
    min_range = None
    for id, a in aircrafts.items():
        if not min_range:
            min_range = {
                id: a['name'],
                'range': a['range']
            }
        else:
            if a['range'] < min_range['range']:
                min_range = {
                id: a['name'],
                'range': a['range']
            }

    logger.debug(
        'aircraft with minimum range {}'
        .format(min_range)
    )
    min_range.pop('range')

    return min_range


def assign_aircraft_to_route(aircrafts, distance_to_fly, default_aircraft):
    regulated_distance = 1.1 * distance_to_fly  # 10% margin to include challenging airports
    # Loop on all aircrafts and select all that can make this distance
    proposed_aircrafts = {}
    for (ida, aircraft) in aircrafts.items():
        if aircraft['range'] >= regulated_distance \
                >= aircraft['range'] * MINIMUM_FLIGHT_PERCENT_DISTANCE / 100:
            proposed_aircrafts[ida] = aircraft['name']

    if len(proposed_aircrafts) == 0:
        logger.warning('no aircraft assigned, assigning default aircraft')
        logger.warning(
            'regulated distance: {}'
                .format(regulated_distance)
        )
        proposed_aircrafts = default_aircraft
    # logger.debug(
    #     'distance {}, proposed aircraft {}'
    #     .format(regulated_distance, proposed_aircrafts)
    # )

    return proposed_aircrafts


def select_flight(flights, visited):
    selected_flights = sorted(
        flights,
        key=lambda x: visited.get(x.arr, 0)
    )
    min_visited = visited.get(
        selected_flights[0].arr, 0
    )
    max_visited = visited.get(
        selected_flights[-1].arr, 0
    )
    delta = max_visited - min_visited
    logger.debug('delta visited: {}'.format(delta))
    if delta > MAXIMUM_VISITED_DIFFERENCE:
        logger.debug('clipping highest visited destination')
        selected_flights = [
            f for f in selected_flights
            if visited.get(f.arr, 0) - min_visited <= MAXIMUM_VISITED_DIFFERENCE
        ]
        flight = random.choice(selected_flights)
    else:
        flight = random.choice(flights)

    return flight



class Airline:
    def _empty_init(self):
        self.name = None
        self.code = None
        self.grades = {}
        self.aircrafts = {}
        self.airports = {}
        self.flights = {}
        self._routes_tree = {}
        self.nsave = 0

    def __init__(self, hub=None, config_file=None):
        self._empty_init()

        if not hub and not config_file:
            return

        try:
            with open(config_file, 'r') as fc:
                config_str = '[DEFAULT]\n' + fc.read()
        except Exception as e:
            logger.error(
                'problem with Airline config_file {}. '
                'err={}'
                .format(config_file, e)
            )
        new_config_str = []
        for s in config_str.split('\n'):
            if 'PAYLEVEL' in s:
                _, num_jump_grade = s.split('=')
                num, jump, grade = num_jump_grade.split(',')
                s = '='.join(
                    ['PAYLEVEL_{}'.format(num),
                     ','.join([jump, grade])
                    ]
                )
            new_config_str.append(s)

        config = configparser.ConfigParser()
        config.read_string('\n'.join(new_config_str))

        name = config['DEFAULT'].get('NAME', None)
        code = config['DEFAULT'].get('CODE', None)
        grades = {}
        for k, value in config['DEFAULT'].items():
            if 'paylevel' in k:
                level = k.split('_')[-1]
                hours, title = value.split(',')
                level = int(level)
                hours = float(hours)
                grades[level] = Grade(hours=hours, title=title.rstrip())
        logger.debug(
            'company name: {}, code: {}, grades: {}'
            .format(name, code, grades)
        )
        self.name = name
        self.code = code
        self.grades = grades

        if not config['DEFAULT'].get('fleet', None):
            logger.error('add "FLEET" path key in company cfg file')
            exit(1)
        if not config['DEFAULT'].get('schedule', None):
            logger.error('add "SCHEDULE" path key in company cfg file')
            exit(1)

        # Loading FSX airports from MakeRunways file r5.csv. Storing data in an airports
        # dictionary. Usage: airports[icao] = (lat, lon)
        file = 'r5.csv'  # runways.xml
        logger.debug('reading FSX data file {}'.format(file))
        self.airports = load_fsx_data(FSX_DIRECTORY + os.sep + file)
        self.hub = hub

        self.progression, self.aircrafts = \
            load_fleet(config['DEFAULT'].get('fleet'))
        self.default_aircraft = find_min_range_aircraft(self.aircrafts)
        self.flights = self._build_routes(config['DEFAULT'].get('schedule'), print_to_file=True)

    def get_company_data(self):
        return (self.name, self.code, [x.get_data() for x in self.pilots],
                self.grades, self.aircrafts, self.flights)

    def _get_airport_longitude(self, icao):
        return self.airports[icao][1]

    def show_aircraft(self):
        for a, data in self.aicrafts:
            print(
                'aircraft {}, data {}'
                .format(a, data)
            )

    def get_aircraft_ktas(self, aircraft_id):
        return self.aircrafts[aircraft_id]['ktas']

    def get_aircraft_name(self, aircraft_id):
        return self.aircrafts[aircraft_id]['name']

    def get_aircraft_range(self, aircraft_id):
        return self.aircrafts[aircraft_id]['range']

    def _build_routes(self, file_schedule, print_to_file=False):
        logger.debug("building routes")
        # Reading full flight schedule from FSC scheduling file
        comments = [';']
        # flights are stored in a dictionary as Flight namedtuple (id, dep, arr, time_lt, distance, aircrafts)
        # flights[idx] = (id, dep, arr, local_lt, distance, aicrafts(=[])). If no local
        # departure time is given a custom departure is set based on flight time and aircraft preparation time.
        # idx is just an integer index, not related to flight id.
        logger.debug('reading schedule file {}'.format(file_schedule))
        flights = {}
        key = 0
        with open(file_schedule, 'r') as fin:
            for line in fin:
                line = line.rstrip()  # Removing final \n in line
                if line[0] not in comments:
                    flight_text = line.split('=')[1]
                    (flight_number, dep, arr, size, hhmm_lt, *other) = flight_text.split(',')
                    logger.debug(
                        'flight nr {}, dep {}, arr {}'
                        .format(flight_number, dep, arr)
                    )
                    # other can contain flight info, so it should be checked
                    Pdep = Point(self.airports[dep][0], self.airports[dep][1])
                    Parr = Point(self.airports[arr][0], self.airports[arr][1])
                    D = distance(Pdep, Parr)
                    aircrafts = assign_aircraft_to_route(self.aircrafts, D, self.default_aircraft)
                    flight = Flight(id=flight_number, arr=arr, dep=dep,
                                    time_lt=time(hour=int(hhmm_lt[0:2]), minute=int(hhmm_lt[2:])),
                                    distance=D, aircraft=aircrafts)
                    flights[key] = flight
                    key = key + 1
        
                    new_flights = [x for x in other[1:] if x != '']
                    if new_flights:
                        arr = new_flights[0]
                        Parr = Point(self.airports[arr][0], self.airports[arr][1])
                        D = distance(Pdep, Parr)
                        aircrafts = assign_aircraft_to_route(
                            self.aircrafts, D, self.default_aircraft
                        )
                        flight = Flight(id=flight_number, dep=arr, arr=arr,
                                        time_lt=time(hour=17, minute=0),
                                        distance=D, aircraft=aircrafts)
                        flights[key] = flight
                        key = key + 1
                        for i in range(1, len(new_flights)):
                            dep = new_flights[i-1]
                            arr = new_flights[i]
                            Pdep = Point(self.airports[dep][0], self.airports[dep][1])
                            Parr = Point(self.airports[arr][0], self.airports[arr][1])
                            D = distance(Pdep, Parr)
                            aircrafts = assign_aircraft_to_route(self.aircrafts, D, self.default_aircraft)
                            aircraft_id = list(aircrafts.keys())[0]
                            ktas = self.get_aircraft_ktas(aircraft_id)
                            dep_time = ceil(AIRCRAFT_TURNOVER_HRS+ceil(D/ktas))

                            flight = Flight(id=flight_number, dep=dep, arr=arr,
                                            time_lt=time(hour=dep_time, minute=0),
                                            distance=D, aircraft=aircrafts)
                            flights[key] = flight
                            key = key + 1

        for (k, flight) in flights.items():
            # Building routes tree
            flight_no, dep, arr, etd_lt, D, _ = flight
            if dep in self._routes_tree.keys():
                # ok, already in the tree, adding the new destination tuple (flight_no, arr)
                self._routes_tree[dep].append(flights[k])
            else:
                self._routes_tree[dep] = [flights[k]]

        if print_to_file:
            file_out = 'aircraft_routes.txt'
            logger.debug('printing route with aircraft to file {}'.format(file_out))
            fout = open(file_out, 'w')

            for (k, flight) in flights.items():
                flight_no, dep, arr, etd_lt, D, _ = flight
                aircrafts = assign_aircraft_to_route(self.aircrafts, D, self.default_aircraft)
                line = '{} {} ({} LT)->{} {} nm {}'.format(flight_no, dep, etd_lt, arr, D, aircrafts)
                fout.write(line+'\n')
                flights[k] = Flight(id=flight_no, dep=dep, arr=arr, time_lt=etd_lt, distance=D, aircraft=aircrafts)

            fout.close()

        logger.debug('found {} flights'.format(len(flights)))
        logger.debug('done')

        return flights

    def get_all_connections_from(self, airport_icao):
        return self._routes_tree[airport_icao]

    def assign_aircraft(self, pilot):
        if pilot.get('aircraft_id') is None:
            pilot.set_aircraft(
                list(self.aircrafts.keys())[0]
            )
        else:
            paid = pilot.get('aircraft_id')
            number_of_flights = pilot.get_flight_with_aircraft(
                paid
            )
            if number_of_flights > MINIMUM_FLIGHTS_BEFORE_PROMOTION:
                idx = self.progression.index(paid)
                if idx < len(self.progression):
                    pilot.set_aircraft(self.progression[idx + 1])
                    logger.info(
                        'Congratulations! You have upgraded to {}'
                        .format(self.progression[idx + 1])
                    )

        return pilot

    def assign_grade(self, pilot):
        pilot_hours = pilot.get('hours')
        diff = pilot_hours * \
             (-pilot_hours + self.grades[1].hours)
        if diff >= 0:
            pilot.grade = self.grades[1].title
            return
        for i in range(1,len(self.grades)):
            diff = (pilot_hours - self.grades[i-1].hours) * \
                   (-pilot_hours + self.grades[i].hours)
            if diff >= 0:
                pilot.grade = self.grades[i].title
                return
        print(pilot.grade.lower())
        if 'captain' in pilot.grade.lower() and not pilot.get('upgraded'):
            pilot.upgrade()
            pilot.set_aircraft(self.progression[0])
            logger.info(
                'Congratulations! You have been promoted to the rank of Captain! '
                'You have been reassigned to aircraft {}'
                .format(pilot.set_aircraft(self.progression[0]))
            )

    def assign_roster(self, pilot, start_date):
        """
        The roster is found in the following way: first a random flight is selected form the __routes_tree base on the
        last pilot position. The roster starting time is the flight departure minus one hour. Then a random sequence of
        flights is generated until the flight time is equal to the maximum limitation. Any path is removed from the
        __routes_tree so the pilot can flight at least once to all airports in the route network. Promotion to captain
        is allowed only after one full rotation.

        The flight time limitations (FTL) are based on 14 CFR § 91.1059:
        Maximum
        (1) 500 hours in any calendar quarter;
        (2) 800 hours in any two consecutive calendar quarters;
        (3) 1,400 hours in any calendar year.
        NOTE: 1-4 5-8 9-12
              400 400 400    satisfy both (1), (2) and (3)
                                                                    Normal duty	    Extension of flight time
        Minimum Rest Immediately Before Duty	                    10 Hours	    10 Hours.
        Duty Period	                                                Up to 14 Hours	Up to 14 Hours.
        Flight Time For 2 Pilots	                                Up to 10 Hours	Exceeding 10 Hours up to 12 Hours.
        Minimum After Duty Rest	                                    10 Hours	    12 Hours.
        Minimum After Duty Rest Period for Multi-Time Zone Flights	14 Hours	    18 Hours.
        """
        day = start_date
        random.seed()

        active_pilot_acft_id = pilot.get('aircraft_id')
        dep_airport = pilot.get('last_airport')

        flights = [f for f in self.get_all_connections_from(dep_airport)
                   if active_pilot_acft_id in list(f.aircraft.keys())]

        presentation = timedelta(hours=PRESENTATION_HRS)
        speed = self.get_aircraft_ktas(active_pilot_acft_id)

        visited = pilot.get_visited()
        schedule = {}
        schedule.setdefault('start', None)
        roster = schedule.setdefault('roster', [])
        total_ft = 0
        set_day = True
        block_time = PRESENTATION_HRS
        while True:
            flight = select_flight(flights, pilot.get_visited())
            ft = flight.distance/speed
            if set_day:
                set_day = False
                day = datetime.combine(day.date(), flight.time_lt)
                dep_utc_time = datetime.combine(
                    day,
                    flight.time_lt
                )
            else:
                previous_flight = roster[-1].arr_lt
                dep_utc_time = datetime.combine(
                    previous_flight.date(),
                    flight.time_lt
                )
            if not schedule.get('start'):
                schedule.update(
                    {
                        'start': day - presentation
                    }
                )
            arr_utc_time = dep_utc_time + timedelta(hours=ft)
            total_ft += ft
            if total_ft > MAXIMUM_FLIGHT_TIME_HRS:
                logger.debug(
                    'reached maximum flight hours {}({})'
                    .format(total_ft, MAXIMUM_FLIGHT_TIME_HRS)
                )
                break
            arr_utc_time = arr_utc_time + timedelta(minutes=AIRCRAFT_TURNOVER_HRS)
            if len(roster) == 0:
                delta = 0
            else:
                delta = (dep_utc_time  - roster[-1].arr_lt).total_seconds()/3600.0
            block_time = block_time + ft + delta
            if block_time > MAXIMUM_BLOCK_HOURS:
                logger.debug(
                    'reached maximum block hours {}({})'
                        .format(block_time, MAXIMUM_BLOCK_HOURS)
                )
                break
            new_dep_airport = flight.arr
            nd = visited.setdefault(flight.dep, 0) + 1
            na = visited.setdefault(flight.arr, 0) + 1
            visited.update({flight.dep: nd})
            visited.update({flight.arr: na})
            pilot.update_visited(visited)
            roster.append(
                Schedule(
                    id='{}{}'.format(self.code, flight.id),
                    dep=flight.dep, arr=flight.arr,
                    dep_lt=dep_utc_time, arr_lt=arr_utc_time,
                    block_time=block_time
                )
            )
            schedule.update(
                {
                    'roster': roster
                }
            )
            flights = \
                [f for f in self.get_all_connections_from(new_dep_airport)
                 if active_pilot_acft_id in list(f.aircraft.keys()) and
                 f.time_lt >= arr_utc_time.time()]
            if len(flights) == 0:
                # no flights. Pilot stops till next day.
                logger.debug(
                    'no more flights for the day'
                )
                break

        logger.debug(
            'Schedule for {}'
            .format(nice_date(day))
        )
        for r in schedule.get('roster'):
            logger.debug(
                '{date} {flight_no} {dep} {arr}'
                .format(
                    date=nice_datetime(r.arr_lt.date()),
                    dep=r.dep, arr=r.arr,
                    flight_no='{}{}'.format(self.code, r.id)
                )
            )
        logger.debug(
            'Total flight time: {} hours'
              .format(total_ft)
        )
        schedule.setdefault(
            'last_airport',
            roster[-1].arr
        )

        return schedule

    def format_schedule(self, schedule, file_out):
        header = ['Flt. Nr.\t\tDep\t\tArr\t\tSTD(LT)\t\t\tSTA(LT)\t\t\tBlk. Hrs.\tStart',
                  '----------------------------------------------------------------------------------------']
        #          AT752       GMMN    EGLL    2020-03-01 07:00    10:30      03:30        06:30
        #          AT775       EGLL    GMMN    2020-03-01 11:25    15:00      06:00
        #          REPOSITION TO GMME                                         08:30                   16:00
        #          AT063       GMME    LIML    2020-03-02 10:45    14:45      04:00        14:00
        line = []
        for f in schedule.get('roster'):
            line.append(
                '\t{flight_no:4s}\t\t{dep}\t{arr}\t{dep_time}\t{arr_time}\t{block:3.1f}\t\t{start}'
                .format(
                    flight_no=f.id, dep=f.dep,
                    arr=f.arr,
                    dep_time=nice_datetime(f.dep_lt),
                    arr_time=nice_datetime(f.arr_lt),
                    block=f.block_time,
                    start=nice_datetime(schedule.get('start')) if len(line)==0 else ''
                )
            )

        text = '\n'.join(header + line)

        fout = open(file_out, 'w')
        fout.write(text)
        fout.close()
