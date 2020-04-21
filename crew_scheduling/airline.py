import pickle
import collections
import yaml
import datetime
import logging
import random
import os
import configparser
from math import ceil
from crew_scheduling.point import Point, distance


logger = logging.getLogger('crew_scheduler.' + __name__)

Grade = collections.namedtuple('Grade', 'hours title')
Flight = collections.namedtuple('Flight', 'id dep arr time_lt distance aircraft')
# Aircraft = collections.namedtuple('Aircraft', 'id name ktas range')

MINIMUM_AIRCRAFT_PREPARATION_TIME_HRS = 1.0
MINIMUM_FLIGHT_PERCENT_DISTANCE= 10
MINIMUM_FLIGHT_TIME_DISTANCE_HRS = 5/60
FSX_DIRECTORY = r'..\data\FSX'
MAXIMUM_FLIGHT_TIME_HRS = 14.0


def lmt2utc(latitude_deg, lmt):
    deltat = datetime.timedelta(hours=latitude_deg/15.0)
    utc = lmt - deltat

    return utc


def utc2lmt(latitude_deg, utc):
    deltat = datetime.timedelta(hours=latitude_deg/15.0)
    lmt = utc + deltat

    return lmt


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
    logger.debug('read {} aircrafts'.format(len(aircrafts)))
    for a, data in aircrafts.items():
        logger.debug(
            'aicraft {}, data {}'
            .format(a, data)
        )
    logger.info('done')

    return aircrafts


def find_min_range_aircraft(aircrafts):
    min_range = None
    for id, a in aircrafts.items():
        if not min_range:
            min_range = a
        else:
            if a['range'] < min_range['range']:
                min_range = a

    logger.debug(
        'aircraft with minimum range {}'
        .format(min_range)
    )

    return min_range


def assign_aircraft_to_route(aircrafts, distance_to_fly, default_aircraft):
    regulated_distance = 1.1 * distance_to_fly  # 10% margin to include challenging airports
    # Loop on all aircrafts and select all that can make this distance
    proposed_aircrafts = {}
    for (ida, aircraft) in aircrafts.items():
        if aircraft['range'] >= regulated_distance \
                >= aircraft['range'] * MINIMUM_FLIGHT_PERCENT_DISTANCE / 100:
            # if aircraft['range'] >= regulated_distance \
            #         >= aircraft['ktas'] * MINIMUM_FLIGHT_TIME_DISTANCE_HRS:
            proposed_aircrafts[ida] = aircraft['name']

    if len(proposed_aircrafts) == 0:
        logger.warning('no aircraft assigned, assigning default aircraft')
        logger.warning(
            'regulated distance: {}'
                .format(regulated_distance)
        )
        proposed_aircrafts = default_aircraft

    logger.debug(
        'distance {}, proposed aircraft {}'
        .format(regulated_distance, proposed_aircrafts)
    )

    return proposed_aircrafts


class Airline:
    def _empty_init(self):
        self.name = None
        self.code = None
        self.grades = {}
        self.pilots = []
        self.aircrafts = {}
        self.airports = {}
        self.flights = {}
        self.active_pilot = None
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
        file = 'r5.csv' #  runways.xml
        logger.debug('reading FSX data file {}'.format(file))
        self.airports = load_fsx_data(FSX_DIRECTORY + os.sep + file)
        self.hub = hub

        self.aircrafts = load_fleet(config['DEFAULT'].get('fleet'))
        self.default_aircraft = find_min_range_aircraft(self.aircrafts)
        self.flights = self.build_routes(config['DEFAULT'].get('schedule'), print_to_file=True)

    def show_pilots(self):
        print('company pilots:')
        if len(self.pilots) == 0:
            print('no pilots yet!')
            return

        for p in self.pilots:
            if p is self.active_pilot:
                print('{} (*)'.format(p.get_data()))
            else:
                print('{}'.format(p.get_data()))

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

    def pickle(self):
        file_save = 'airline.{}.sts'.format(self.nsave)
        self.nsave += 1
        f = open(file_save, 'wb')
        pickle.dump(self, f)
        f.close()

    @staticmethod
    def unpickle(file_save):
        try:
            with open(file_save, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error('unpickle err={}'.format(e))
            exit(1)

    def build_routes(self, file_schedule, print_to_file=False):
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
                    logging.debug(
                        'flight nr {}, dep {}, arr {}'
                        .format(flight_number, dep, arr)
                    )
                    # other can contain flight info, so it should be checked
                    Pdep = Point(self.airports[dep][0], self.airports[dep][1])
                    Parr = Point(self.airports[arr][0], self.airports[arr][1])
                    D = distance(Pdep, Parr)
                    aircrafts = assign_aircraft_to_route(self.aircrafts, D, self.default_aircraft)
                    flight = Flight(id=flight_number, arr=arr, dep=dep,
                                    time_lt=datetime.time(hour=int(hhmm_lt[0:2]), minute=int(hhmm_lt[2:])),
                                    distance=D, aircraft=aircrafts)
                    flights[key] = flight
                    key = key + 1
        
                    new_flights = [x for x in other[1:] if x != '']
                    if new_flights:
                        arr = new_flights[0]
                        Parr = Point(self.airports[arr][0], self.airports[arr][1])
                        D = distance(Pdep, Parr)
                        aircrafts = assign_aircraft_to_route(self.aircrafts, D, self.default_aircraft)
                        flight = Flight(id=flight_number, dep=arr, arr=arr,
                                        time_lt=datetime.time(hour=17, minute=0),
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
                            dep_time = ceil(MINIMUM_AIRCRAFT_PREPARATION_TIME_HRS+ceil(D/ktas))

                            flight = Flight(id=flight_number, dep=dep, arr=arr,
                                            time_lt=datetime.time(hour=dep_time, minute=0),
                                            distance=D, aircraft=aircrafts)
                            flights[key] = flight
                            key = key + 1

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

                # Building routes tree
                if dep in self._routes_tree.keys():
                    # ok, already in the tree, adding the new destination tuple (flight_no, arr)
                    self._routes_tree[dep].append(flights[k])
                else:
                    self._routes_tree[dep] = [flights[k]]

            fout.close()

        logger.debug('found {} flights'.format(len(flights)))
        logger.debug('done')

        return flights

    def get_all_connections_from(self, airport_icao):
        return self._routes_tree[airport_icao]

# PILOT UTILITIES
    def get_pilots(self):
        return self.pilots

    def get_active_pilot(self):
        return self.active_pilot

    def get_active_pilot_aircraft(self):
        return self.active_pilot.aircraft

    def set_active_pilot(self, active_pilot):
        self.active_pilot = active_pilot

    def assign_pilot(self, new_pilot):
        self.pilots.append(new_pilot)
        
    def assign_aircraft_to_active_pilot(self, pilot=None, aircraft=None):
        if aircraft is None and pilot is None:
            # assign by default first aircraft in fleet.yml file
            self.active_pilot.aircraft = list(self.aircrafts.keys())[0] 
        else:
            for p in range(len(self.pilots)):
                if pilot.name == self.pilots[p].name:
                    self.pilots[p].aircraft = aircraft

    def assign_grade(self):
        # Check to see if an active pilot exists
        if self.active_pilot is None:
            logger.error('assign an active pilot first')
            exit(1)

        diff = self.active_pilot.hours * \
             (-self.active_pilot.hours + self.grades[1].hours)
        if diff >= 0:
            self.active_pilot.grade = self.grades[1].title
            return
        for i in range(1,len(self.grades)):
            diff = (self.active_pilot.hours - self.grades[i-1].hours) * \
                   (-self.active_pilot.hours + self.grades[i].hours)
            if diff >= 0:
                self.active_pilot.grade = self.grades[i].title
                return 

    def assign_roster(self):
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
        import time

        random.seed()

        active_pilot_acft_id = self.get_active_pilot_aircraft()
        dep_airport = self.hub

        # selective only flights for current active pilot aircraft
        flights = [f for f in self.get_all_connections_from(dep_airport)
                   if active_pilot_acft_id in list(f.aircraft.keys())]
        # suffling flights
        # random.shuffle(flights)

        day = datetime.date.today()
        delta = datetime.timedelta(hours=1)
        # time before first presentation at crew dispatcher
        flight_departure = datetime.datetime.combine(day, flights[0].time_lt)
        arr_airport = flights[0].arr
        start_roster_time = flight_departure - delta
        dep_utc_time = lmt2utc(self._get_airport_longitude(dep_airport),
                               flight_departure)
        logger.info('Start roster (all times are LMT): {}'
              .format(start_roster_time.isoformat()))
        speed = self.get_aircraft_ktas(self.get_active_pilot_aircraft())
        ft = flights[0].distance/speed
        logger.debug(
            '{} {} {} {}'
            .format(flights[0].dep, flights[0].arr,
                    dep_utc_time, flights[0].id))
        del flights[0]  # first flight is starting flight. Removing from list.

        roster = []
        build_roster = True
        total_ft = ft
        flights = [f for f in self.get_all_connections_from(arr_airport)
                   if active_pilot_acft_id in list(f.aircraft.keys())]
        print(flights)
        exit()
        while build_roster:
            flight = random.choice(flights)
            ft = flight.distance/speed
            arr_utc_time = dep_utc_time + datetime.timedelta(hours=ft)
            # arr_lmt_time =
            # utc2lmt(self.getAirportLongitude(flight.arr), arr_utc_time)
            total_ft = total_ft \
                + (arr_utc_time - dep_utc_time).total_seconds()/3600.0
            new_dep_airport = flight.arr
            if total_ft < MAXIMUM_FLIGHT_TIME_HRS:
                roster.append(flight)
                # print(ft)
                flights = \
                    [f for f in self.get_all_connections_from(new_dep_airport)
                     if active_pilot_acft_id in list(f.aircraft.keys())]
            else:
                build_roster = False

        for r in roster:
            logger.debug(
                '{2} {3} {0} {1}'
                .format(datetime.datetime.combine(day, r.time_lt).isoformat(),
                        r.id, r.dep, r.arr)
            )
        logger.debug('Total flight time: {} hours'.format(total_ft))


def format_schedule(flights):
    header = ['Flt. Nr.    Dep     Arr     STD(LT)             STA(LT)    Blk. Hrs.    Start      End  ',
              '----------------------------------------------------------------------------------------']
    #          AT752       GMMN    EGLL    2020-03-01 07:00    10:30      03:30        06:30
    #          AT775       EGLL    GMMN    2020-03-01 11:25    15:00      06:00
    #          REPOSITION TO GMME                                         08:30                   16:00
    #          AT063       GMME    LIML    2020-03-02 10:45    14:45      04:00        14:00
    line = []
    for d, a in flights:
        line.append(
            '{dep}  {arr}'.format(dep=d, arr=a)
        )

    text = '\n'.join(header + line)

    return text