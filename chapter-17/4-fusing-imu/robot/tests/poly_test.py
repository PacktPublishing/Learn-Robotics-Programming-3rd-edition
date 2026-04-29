from shapely import LineString
from shapely.geometry import MultiPoint, Polygon
import numpy as np
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

vertices = [
    (0, 1500),
    (1500, 1500),
    (1500, 500),
    (1000, 500),
    (1000, 0),
    (0, 0)
]

test_area = Polygon(
    vertices
)

population_size = 20000
logging.info(f"Creating random data. {population_size} points.")
points = np.column_stack((
    np.random.uniform(0, 1500, population_size),
    np.random.uniform(0, 1500, population_size),
    np.random.uniform(0, 2 * np.pi, population_size)
))


def filter_with_shapely(points):
    logging.info("Filtering points - converting to shapely")

    s_points = MultiPoint(points)

    logging.info("Intersecting")

    matching = s_points.intersection(test_area)
    logging.info(f"Matching points: {len(matching.geoms)} of {len(s_points.geoms)}")
    logging.info("Double checking ")
    all_points_contained = test_area.contains(s_points)
    matching_points_contained =  test_area.contains(matching)
    logging.info(f"Check results: all points contained {all_points_contained}, matching points contained {matching_points_contained}")
    logging.info("Converting back to numpy points")
    n_points = np.array([[point.x, point.y, point.z] for point in matching.geoms])
    # n_points = np.asarray(matching.coords) #np.array([[point.x, point.y, point.z] for point in matching.geoms])
    logging.info(f"First few points are {n_points[0:10].tolist()}")

def filter_with_conditionals(points):
    logging.info(f"Points shape: {points.shape}")
    logging.info(f"First few raw points are {points[0:10].tolist()}")
    # filtered = points[not(points[:,0] > 1000 and points[:,1] > 1000)][0]
    likely_in_cutout = np.logical_not(np.logical_and(np.greater(points[:, 0], 1000),np.greater(points[:, 1], 1000)))
    filtered = points[likely_in_cutout]
    logging.info(f"Matching points: {len(filtered)} or {len(points)}")
    logging.info(f"First few points are {filtered[0:10].tolist()}")

logging.info("Filtering with conditionals")
filter_with_conditionals(points)
logging.info("Filtering with shapely")
filter_with_shapely(points)

# Shapely has a PIwheel! Yay.
# On the pi - the creating points too longer than counting.
# KEY QUESTION - do I still need numpy?
# Can I do rotations/translations?
# Not with theta in place - so we do need ot convert.
# With 200k points, conversion and test took 0.3 s. Creation took 5 seconds.
# Converting back to numpy took 0.3s though - that is a long time on the robot.

"""
danny@learnrob3:~ $ robotpython poly_test.py
2025-04-08 15:52:19,202 - INFO - Creating random data. 200000 points.
2025-04-08 15:52:19,236 - INFO - Filtering points - converting to shapely
2025-04-08 15:52:19,702 - INFO - Counting contained points
2025-04-08 15:52:19,908 - INFO - Matching points: 177649 of 200000
2025-04-08 15:52:19,908 - INFO - Double checking
2025-04-08 15:52:20,000 - INFO - Check results: all points contained False, matching points contained True
danny@learnrob3:~ $ robotpython poly_test.py
2025-04-08 15:52:22,887 - INFO - Creating random data. 200000 points.
2025-04-08 15:52:22,922 - INFO - Filtering points - converting to shapely
2025-04-08 15:52:23,386 - INFO - Counting contained points
2025-04-08 15:52:23,589 - INFO - Matching points: 177771 of 200000
2025-04-08 15:52:23,589 - INFO - Double checking
2025-04-08 15:52:23,683 - INFO - Check results: all points contained False, matching points contained True


Todo:
- Add shapely into our base packages
- Explain why we introduce it (for geom operations)
- Use the above method
"""

"""
Reran - shaeply points are not what I expected. That and speed is quite different:
2025-04-10 14:44:38,963 - INFO - Creating random data. 20000 points.
2025-04-10 14:44:38,971 - INFO - Filtering with conditionals
2025-04-10 14:44:38,971 - INFO - Points shape: (20000, 3)
2025-04-10 14:44:38,971 - INFO - First few raw points are [[894.6907296570264, 782.0316715079251, 6.270517681496492], [1040.8577850137208, 122.52803900783954, 2.242788934055019], [367.5761557449056, 285.5887510494523, 1.7105426651201565], [945.7206995389125, 695.8044961296891, 5.416103181533591], [1145.9083688025912, 1163.0867696313521, 3.3528764677258382], [5.03195950026053, 222.80607966740112, 3.5477586427886996], [469.81537027465095, 158.63411630491896, 2.2002601620729147], [1187.900959092066, 765.0885538950879, 1.584856800804014], [1002.498572267787, 395.09289837244444, 1.8755239532024763], [1137.3354460688945, 111.2966519804921, 5.423553811738775]]
2025-04-10 14:44:38,971 - INFO - Matching points: 17823 or 20000
2025-04-10 14:44:38,971 - INFO - First few points are [[894.6907296570264, 782.0316715079251, 6.270517681496492], [1040.8577850137208, 122.52803900783954, 2.242788934055019], [367.5761557449056, 285.5887510494523, 1.7105426651201565], [945.7206995389125, 695.8044961296891, 5.416103181533591], [5.03195950026053, 222.80607966740112, 3.5477586427886996], [469.81537027465095, 158.63411630491896, 2.2002601620729147], [1187.900959092066, 765.0885538950879, 1.584856800804014], [1002.498572267787, 395.09289837244444, 1.8755239532024763], [1137.3354460688945, 111.2966519804921, 5.423553811738775], [12.52819621503576, 52.55529845679735, 0.625435270013757]]
2025-04-10 14:44:38,972 - INFO - Filtering with shapely
2025-04-10 14:44:38,972 - INFO - Filtering points - converting to shapely
2025-04-10 14:44:38,983 - INFO - Intersecting
2025-04-10 14:44:38,987 - INFO - Matching points: 17781 of 20000
2025-04-10 14:44:38,987 - INFO - Double checking
2025-04-10 14:44:38,990 - INFO - Check results: all points contained False, matching points contained True
2025-04-10 14:44:38,990 - INFO - Converting back to numpy points
2025-04-10 14:44:39,152 - INFO - First few points are [[0.042015977647746894, 417.57919941322564, 4.215075346897172], [0.10246800740060236, 1355.3355674008735, 6.008159181613371], [0.1281664034920582, 86.92498917059305, 1.0541026502340722], [0.4403480009725902, 1241.2033819066248, 2.5249298100612183], [0.44052676493439025, 309.2902151084845, 2.288759809188251], [0.6303051107189872, 501.21514597844504, 4.517729431915001], [0.6645174913118557, 1116.2657802935976, 4.033154263563013], [0.7071594995754493, 519.2774025512264, 1.5341910498838875], [0.7495928452330158, 1074.1226331076016, 1.378713273929717], [0.8852906180597531, 332.6678127841637, 1.9738452782720297]]

Conditionals - tool less that 1ms. Shapely took 200ms. No comparison. Will get interesting for non co axial boundaries - but we don't have any.
"""
