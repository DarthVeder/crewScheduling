"""
Class to manage a pilot career.

Author: MM
Copyright: 2019 -
License: GPL 3.0
"""


class Pilot:
    def __init__(self, name=None):
        self.name = name
        self.grade = None
        self.aircraft = None
        self.hours = 0.0
        self.hub = None

    def create(self, name):
        self.name = name

    def retrieve(self):
        return self.name, self.aircraft, self.grade, self.hours, self.hub


if __name__ == '__main__':

    new_pilot = Pilot()

    new_pilot.create('Marco Messina')

    print(new_pilot.retrieve())
