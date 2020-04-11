"""
Class to manage an airline company.

Author: Marco Messina
Copyright: 2019 -
Licence: GPL 3.0
"""
import pickle
from pilot import Pilot
import collections
import yaml
import datetime

Grade = collections.namedtuple('Grade', 'hours title')
Flight = collections.namedtuple('Flight', 'id dep arr time_lt distance aircraft')
# Aircraft = collections.namedtuple('Aircraft', 'id name ktas range')

MINIMUM_AIRCRAFT_PREPARATION_TIME_HRS = 1.0
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

class Airline:
    def __init__(self, config_file=None):
        if config_file is None:
            name = None
            code = None
            grades = {}
        else:
            name, code, grades = self.readConfigurationFile(config_file)

        self.name = name
        self.code = code
        self.grades = grades
        self.pilots = []
        self.aircrafts = {}
        self.airports = {}
        self.flights = {}
        self.active_pilot = None
        self.__routes_tree = {}
        self.hub = 'GMMN'

    @staticmethod
    def readConfigurationFile(config_file):
        company_name = ''
        code = ''
        grades = {}
        with open(config_file, 'r') as fin:
            for line in fin:
                # avoiding line staring with ";"
                if line[0] != ';':
                    # trashing out part of line after inline comment starting with ";"
                    line = line.split(';')[0]
                    key, value = line.split('=')
                    if key == 'NAME':
                        company_name = value.rstrip()
                    elif key == 'CODE':
                        code = value.rstrip()
                    elif key == 'PAYLEVEL':
                        level,hours,title = value.split(',')
                        level = int(level)
                        hours = float(hours)
                        grades[level] = Grade(hours=hours, title=title.rstrip())
                
        print('Defining new company with:\nName: {}\nCode: {}\nGrades:'.format(company_name, code))
        for key, value in grades.items():
            print('{} Minimum hours: {}'.format(value.title, value.hours))
            
        return company_name, code, grades

    def retrieve(self):
        return (self.name, self.code, [x.retrieve() for x in self.pilots],
                self.grades, self.aircrafts, self.flights)

    @staticmethod
    def assignAircraftToRoute(aircrafts, distance_to_fly):
        regulated_distance = 1.1 * distance_to_fly # 10% margin to include challenging airports
        # Loop on all aircrafts and select all that can make this distance
        proposed_aircrafts = {}

        for (ida, aircraft) in aircrafts.items():
            # the 5/60*ktas is to avoid huge aircraft assigned to small routes
            if aircraft['range'] >= regulated_distance and \
                regulated_distance>=aircraft['ktas']*MINIMUM_FLIGHT_TIME_DISTANCE_HRS:
                proposed_aircrafts[ida] = aircraft['name']

        return proposed_aircrafts

    def getAirportLongitude(self, icao):
        return self.airports[icao][1]

    def loadFleet(self, fleet_file):
        # Parsing Fleet file and saving the fleet in dictionary aircrafts.
        # Usage: aircrafts[id]['name' or 'ktas' or 'range']
        print('Loading fleet...', end="", flush=True)
        with open(fleet_file, 'r') as file:
            aircrafts = yaml.full_load(file)
        self.aircrafts = aircrafts
        print('[OK]')

    def getAircraftKtas(self, aircraft_id):
        return self.aircrafts[aircraft_id]['ktas']

    def getAircraftName(self, aircraft_id):
        return self.aircrafts[aircraft_id]['name']

    def pickle(self):
        f = open('airline.ms', 'wb')
        pickle.dump(self, f)
        f.close()

    @staticmethod
    def unpickle():
        with open('airline.ms', 'rb') as f:
            return pickle.load(f)

    def buildRoutes(self, file_schedule):

        import os
        from math import ceil
        from point import Point, distance


        print("Building routes....", end="", flush=True)
        # Loading FSX airports from MakeRunways file r5.csv. Storing data in an airports
        # dictionary. Usage: airports[icao] = (lat, lon)
        file = 'r5.csv'
        with open(FSX_DIRECTORY + os.sep + file, 'r') as fin:
            for line in fin:
                # Inserting only the first runway and its lat, lon. It is assumed 
                # the airport has the same coordinates as the runway.
                (icao, hdg, lat, lon, *trash ) = line.split(',')
                if icao not in self.airports:
                    self.airports[icao] = (float(lat), float(lon))
                    
        # Reading full flight schedule from FSC scheduling file
        comments = [';']
        # flights are stored in a dictionary as Flight namedtuple (id, dep, arr, time_lt, distance, aircrafts)
        # flights[idx] = (id, dep, arr, local_lt, distance, aicrafts(=[])). If no local
        # departure time is given a custom departure is set based on flight time and aircraft preparation time.
        # idx is just an integer index, not related to flight id.
        flights = {}
        key = 0
        with open(file_schedule, 'r') as fin:
            for line in fin:
                line = line.rstrip() # Removing final \n in line
                if line[0] not in comments:
                    flight_text = line.split('=')[1]
                    (flight_number, dep, arr, size, hhmm_lt, *other) = flight_text.split(',')
                    # other can contain other flight info, so it should be checked
                    Pdep = Point(self.airports[dep][0], self.airports[dep][1])
                    Parr = Point(self.airports[arr][0], self.airports[arr][1])
                    D = distance(Pdep, Parr)
                    flight = Flight(id=flight_number, arr=arr, dep=dep,
                                    time_lt=datetime.time(hour=int(hhmm_lt[0:2]), minute=int(hhmm_lt[2:])),
                                    distance=D, aircraft=None)
                    flights[key] = flight
                    key = key + 1
        
                    new_flights = [x for x in other[1:] if x != '']
                    if new_flights:
                        arr = new_flights[0]
                        Parr = Point(self.airports[arr][0], self.airports[arr][1])
                        D = distance(Pdep, Parr)
                        flight = Flight(id=flight_number, dep=arr, arr=arr,
                                        time_lt=datetime.time(hour=17, minute=0),
                                        distance=D, aircraft=None)
                        flights[key] = flight
                        key = key + 1
                        for i in range(1, len(new_flights)):
                            dep = new_flights[i-1]
                            arr = new_flights[i]
                            Pdep = Point(self.airports[dep][0], self.airports[dep][1])
                            Parr = Point(self.airports[arr][0], self.airports[arr][1])
                            D = distance(Pdep, Parr)
                            aircrafts = self.assignAircraftToRoute(self.aircrafts, D)
                            aircraft_id = list(aircrafts.keys())[0]
                            ktas = self.getAircraftKtas(aircraft_id)
                            dep_time = ceil(MINIMUM_AIRCRAFT_PREPARATION_TIME_HRS+ceil(D/ktas))

                            flight = Flight(id=flight_number, dep=dep, arr=arr,
                                            time_lt=datetime.time(hour=dep_time, minute=0),
                                            distance=D, aircraft=None)
                            flights[key] = flight
                            key = key + 1

        file_out = 'aircraft_routes.txt'
        fout = open(file_out, 'w')

        for (k, flight) in flights.items():
            flight_no, dep, arr, etd_lt, D, _ = flight
            aircrafts = self.assignAircraftToRoute(self.aircrafts, D)
            line = '{} {} ({} LT)->{} {} nm {}'.format(flight_no, dep, etd_lt, arr, D, aircrafts)
            fout.write(line+'\n')
            flights[k] = Flight(id=flight_no, dep=dep, arr=arr, time_lt=etd_lt, distance=D, aircraft=aircrafts)

            # Building routes tree
            if dep in self.__routes_tree.keys():
                # ok, already in the tree, adding the new destination tuple (flight_no, arr)
                self.__routes_tree[dep].append(flights[k])
            else:
                self.__routes_tree[dep] = [flights[k]]

        # for k, value in flights.items():
        #    print(k,value)

        fout.close()
        
        self.flights = flights
        print('[OK]')

    def getAllConnectionsFrom(self, airport_icao):
        return self.__routes_tree[airport_icao]

# PILOT UTILITIES
    def getActivePilotAircraft(self):
        return self.active_pilot.aircraft

    def setActivePilot(self, active_pilot):
        self.active_pilot = active_pilot

    def assignPilot(self, new_pilot):
        self.pilots.append(new_pilot)
        
    def assignAircraftToActivePilot(self, pilot=None, aircraft=None):
        if aircraft is None and pilot is None:
            # assign by default first aircraft in fleet.yml file
            self.active_pilot.aircraft = list(self.aircrafts.keys())[0] 
        else:
            for p in range(len(self.pilots)):
                if pilot.name == self.pilots[p].name:
                    self.pilots[p].aircraft = aircraft

    def assignGrade(self):
        # Check to see if an active pilot exists
        if self.active_pilot is None:
            print('ERROR: assign an active pilot first')
            sys.exit()

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

    def assignRoster(self):
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
        import random
        random.seed()

        active_pilot_acft_id = self.getActivePilotAircraft()
        dep_airport = self.hub

        # selective only flights for current active pilot aircraft
        flights = [f for f in self.getAllConnectionsFrom(dep_airport) if active_pilot_acft_id in list(f.aircraft.keys())]
        # suffling flights
        #random.shuffle(flights)

        day = datetime.date.today()
        delta = datetime.timedelta(hours=1)  # time before first presentation at crew dispatcher
        flight_departure = datetime.datetime.combine(day, flights[0].time_lt)
        arr_airport = flights[0].arr
        start_roster_time = flight_departure - delta
        dep_utc_time = lmt2utc(self.getAirportLongitude(dep_airport), flight_departure)
        print('Start roster (all times are LMT): {}'.format(start_roster_time.isoformat()))
        speed = self.getAircraftKtas(self.getActivePilotAircraft())
        ft = flights[0].distance/speed
        print('{} {} {} {}'.format(flights[0].dep, flights[0].arr, dep_utc_time, flights[0].id))
        del flights[0]  # first flight is starting flight. Removing from list.

        roster = []
        build_roster = True
        total_ft = ft
        flights = [f for f in self.getAllConnectionsFrom(arr_airport) if active_pilot_acft_id in list(f.aircraft.keys())]
        while build_roster:
            flight = random.choice(flights)
            ft = flight.distance/speed
            arr_utc_time = dep_utc_time + datetime.timedelta(hours=ft)
            #arr_lmt_time = utc2lmt(self.getAirportLongitude(flight.arr), arr_utc_time)
            total_ft = total_ft + (arr_utc_time - dep_utc_time).total_seconds()/3600.0
            new_dep_airport = flight.arr
            if total_ft < MAXIMUM_FLIGHT_TIME_HRS:
                roster.append(flight)
                #print(ft)
                flights = [f for f in self.getAllConnectionsFrom(new_dep_airport) if active_pilot_acft_id in list(f.aircraft.keys())]
            else:
                build_roster = False

        for r in roster:
            print('{2} {3} {0} {1}'.format(datetime.datetime.combine(day, r.time_lt).isoformat(), r.id, r.dep, r.arr))
        print('Total flight time: {} hours'.format(total_ft))

# if __name__ == '__main__':
#     import sys
#     load = False
#     if not load:
#         company_config_file = 'RoyalAirMaroc.cfg'
#         company_schedule_file = 'RoyalAirMaroc_schedule.txt'
#         company_fleet_file = 'fleet.yml'
#
#         new_company = Airline(company_config_file)
#
#         pilot1 = Pilot('Giovannino Liguori')
#         new_company.assignPilot(pilot1)
#         pilot2 = Pilot('Ibrahim Mustafà')
#         new_company.assignPilot(pilot2)
#
#         new_company.loadFleet(company_fleet_file)
#         new_company.buildRoutes(company_schedule_file)
#         new_company.setActivePilot(pilot1)
#         new_company.assignAircraftToActivePilot()
#         new_company.assignGrade()
#
#         # Saving to file
#         new_company.pickle()
#     else:
#         # To recover from file:
#         new_company = Airline()
#         new_company = Airline.unpickle()
#
#         # new_company.assignAircraftToPilot()
#         # new_company.assignGrade()
#
#     print('Active pilot: {}'.format(new_company.active_pilot.retrieve()))
#
#     new_company.assignRoster()

 
