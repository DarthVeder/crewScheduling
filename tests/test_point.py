import unittest
from crew_scheduling.point import Point, distance


distance_ok = 3787.049908422731


class TestPoint(unittest.TestCase):
    def test_distance(self):
        P1 = Point(0, 0)
        P2 = Point(34.4, 56.77)

        D = distance(P2, P1)

        self.assertEqual(D, distance_ok)


if __name__ == '__main__':
    unittest.main()