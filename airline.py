"""
Class to manage an airline company.

Author: MM
Copyright: 2019 -
Licensce: GPL 3.0
"""
import pickle
from pilot import Pilot
import collections
import yaml

Grade = collections.namedtuple('Grade', 'hours title')
Flight = collections.namedtuple('Flight', 'id dep arr time_lt distance')

class Airline:
    def __init__(self, config_file = None):
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
    def assignAircraftToRoutes(aircrafts, distance_to_fly):
        regulated_distance = 1.1 * distance_to_fly # 10% margin to include challenging airports
        # First loop to select all aircraft that can make this distance
        proposed_aircraft = {}
        for (ida, aircraft) in aircrafts.items():
            # the 5/60*ktas is to avoid huge aircraft assigned to small routes
            if aircraft['range'] >= regulated_distance and\
                regulated_distance>=aircraft['ktas']*5/60:
                proposed_aircraft[ida] = aircraft['name']

        return proposed_aircraft

    def loadFleet(self, fleet_file):
        # Parsing Fleet file and saving the fleet in dictionary aircrafts.
        # Usage: aircrafts[id]['name' or 'ktas' or 'range']
        print('Loading fleet...', end="", flush=True)
        with open(fleet_file, 'r') as file:
            aircrafts = yaml.full_load(file)
        self.aircrafts = aircrafts
        print('[OK]')
        
    def pickle(self):
        f = open('airline.ms', 'wb')
        pickle.dump(self, f)
        f.close()

    @staticmethod
    def unpickle():
        with open('airline.ms', 'rb') as f:
            return pickle.load(f)

    def buildRoutes(self, file_schedule):
        FSX_DIRECTORY = 'C:\\Microsoft Flight Simulator X'
        import os
        from point import Point, distance

        print("Building routes....", end="", flush=True)
        # Loading FSX airports from MakeRunways file r5.csv. Storing data in airports
        # dictionary. Usage: airports[icao] = (lat, lon)
        file = 'r5.csv'
        airports = {}
        with open(FSX_DIRECTORY + os.sep+ file, 'r') as fin:
            for line in fin:
                # Inserting only the first runway and its lat, lon. It is assumed 
                # the airport has the same coordinates.
                (icao, hdg, lat, lon, *trash ) = line.split(',')
                if icao not in airports:
                    airports[icao] = (float(lat), float(lon))
                    
        # Reading full flight schedule from FSC scheduling file format
        comments = [';']
        # flights are stored in a dictionary as Flight namedtuple (id, dep, arr, hhmm_lt, distance)
        # flights[id] = (id, dep, arr, local_lt, distance). If no local
        # departure time is given a -1 is set. id is just an integer index.
        flights = {}
        key = 0
        with open(file_schedule, 'r') as fin:
            for line in fin:
                line = line.rstrip() # Removing final \n in line
                if line[0] not in comments:
                    flight_text = line.split('=')[1]
                    (flight_number, dep, arr, size, hhmm_lt, *other) = flight_text.split(',')
                    # other can contain other flight info, so it should be checked
                    Pdep = Point(airports[dep][0], airports[dep][1])
                    Parr = Point(airports[arr][0], airports[arr][1])
                    D = distance(Pdep, Parr)
                    flight = Flight(id=flight_number, arr=arr, dep=dep, time_lt=int(hhmm_lt), distance=D)
                    flights[key] = flight
                    key = key + 1
        
                    new_flights = [x for x in other[1:] if x != '']
                    if new_flights:
                        arr = new_flights[0]
                        #Pdep = Point(airports[dep][0], airports[dep][1])
                        Parr = Point(airports[arr][0], airports[arr][1])
                        D = distance(Pdep, Parr)
                        flight = Flight(id=flight_number, dep=arr, arr=arr, time_lt=-1, distance=D)
                        flights[key] = flight
                        key = key + 1
                        for i in range(1, len(new_flights)):
                            dep = new_flights[i-1]
                            arr = new_flights[i]
                            Pdep = Point(airports[dep][0], airports[dep][1])
                            Parr = Point(airports[arr][0], airports[arr][1])
                            D = distance(Pdep, Parr)
                            flight = Flight(id=flight_number, dep=dep, arr=arr, time_lt=-1, distance=D)
                            flights[key] = flight
                            key = key + 1

        file_out = 'aircraft_routes.txt'
        fout = open(file_out, 'w')

        for (k, flight) in flights.items():
            flight_no, dep, arr, etd_lt, D = flight
            aircraft = self.assignAircraftToRoutes(self.aircrafts, D)
        
            line = '{} {} ({:04d} LT)->{} {} nm {}'.format(flight_no, dep, etd_lt, arr, D, aircraft)
            fout.write(line+'\n')

            # Building routes tree
            if dep in self.__routes_tree.keys():
                # ok, already in the tree, adding the new destination tuple (flight_no, arr)
                self.__routes_tree[dep].append(flight)
            else:
                self.__routes_tree[dep] = [flight]


        # for k, value in flights.items():
        #    print(k,value)

        fout.close()
        
        self.flights = flights
        print('[OK]')
        
#### PILOT UTILITIES
    def setActivePilot(self, active_pilot):
        self.active_pilot = active_pilot

    def assignPilot(self, new_pilot):
        self.pilots.append(new_pilot)
        
    def assignAircraftToPilot(self, pilot=None, aircraft=None):
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
        roster = {}

        last_airport = self.hub

        # first random flight of the day
        idestination = random.randint(0, len(self.__routes_tree[last_airport])-1)
        roster[last_airport] = self.__routes_tree[last_airport][idestination]

        day = time.localtime(time.time()).tm_mday
        ft = 0
        print('Start roster: {} at {}'.format(day, roster[last_airport].time_lt - 100))
        ft = ft + 1


        for k, values in roster.items():
            print(k,values)

if __name__ == '__main__':
    import sys
    load = True
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
   
        # Saving to file
        new_company.pickle()
    else:
        # To recover from file:
        new_company = Airline()
        new_company = Airline.unpickle()

        new_company.assignAircraftToPilot()
        new_company.assignGrade() 

    print('Active pilot: {}'.format(new_company.active_pilot.retrieve()))

    new_company.assignRoster()

 
