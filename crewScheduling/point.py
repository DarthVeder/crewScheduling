"""
Class point. It stores (lat, lon) and perform a simple distance calculation
between two points.

Usage:
P1 = Point(lat, lon)
P2 = Point(lat, lon)
D = distance(P1, P2) = distance(P2, P1)

Author: M. Messina
Copyright: 2019 -
Licence: GPL 3.0
"""

from math import acos, sin, cos, pi

EARTH_RADIUS_NM = 3437.75


class Point:
    """
    Stores coordinates of a point on a sphere as (latitute, longitude)
    in radians.
    Format is a decimal real number (ex -4.667 rad, 5.556 rad).
    """
    def __init__(self, lat_deg, lon_deg):
        self.lat = lat_deg/180.0*pi
        self.lon = lon_deg/180.0*pi

    def setLatitude(self, lat_deg):
        self.lat = lat_deg/180.0*pi

    def setLongitude(self, lon_deg):
        self.lon = lon_deg/180.0*pi


def distance(P1, P2):
    """
    Distance in nm between two points (defined as class Point()) on a sphere
    of radi EARTH_RADIUS_NM. From www.gcmap.com
    """
    theta = P2.lon - P1.lon
    dist = sin(P1.lat)*sin(P2.lat) + cos(P1.lat)*cos(P2.lat)*cos(theta)
    dist = acos(dist)
    dist_nm = dist * EARTH_RADIUS_NM

    return dist_nm


if __name__ == '__main__':
    P1 = Point(0, 0)
    P2 = Point(34.4, 56.77)

    D = distance(P2, P1)

    # print(D) # should be 3787.049908422731, versus WGS84 3,789 nm
    assert(abs(D - 3787.049908422731) < 1e-12), \
        "Something is wrong in distance(P1, P2)"
