from typing import Dict, List

cable_data: Dict[str, Dict[str, List[tuple]]] = {}

# BS7671:2008 table 4F1A
# 60C thermosetting insulated flexible cables with sheath, non-armoured
cable_data["4F1A"] = {}
#    CSA, Two conductors, 3-5 conductors, separate conductors
cable_data["4F1A"]["ratings"] = [
    (4, 30, 26, None),
    (6, 39, 34, None),
    (10, 51, 47, None),
    (16, 73, 63, None),
    (25, 97, 83, None),
    (35, None, 102, 140),
    (50, None, 124, 175),
    (70, None, 158, 216),
    (95, None, 192, 258),
    (120, None, 222, 302),
    (150, None, 255, 347),
    (185, None, 291, 394),
    (240, None, 343, 471),
    (300, None, 394, 541),
    (400, None, None, 644),
    (500, None, None, 738),
    (630, None, None, 861),
]

# CSA, two-core DC, two-core AC, multi-core AC, touching AC, touching DC
cable_data["4F1A"]["voltage_drop"] = [
    (4, 12, 12, 10, None, None),
    (6, 7.8, 7.8, 6.7, None, None),
    (10, 4.6, 4.6, 4.0, None, None),
    (16, 2.9, 2.9, 2.5, None, None),
    (25, 1.8, (1.8, 0.175, 1.85), (1.55, 0.150, 1.55), None, None),
    (35, None, None, (1.10, 0.150, 1.15), 1.31, (1.31, 0.21, 1.32)),
    (50, None, None, (0.83, 0.145, 0.84), 0.91, (0.91, 0.21, 0.93)),
    (70, None, None, (0.57, 0.140, 0.58), 0.64, (0.64, 0.20, 0.67)),
    (95, None, None, (0.42, 0.135, 0.44), 0.49, (0.49, 0.195, 0.53)),
    (120, None, None, (0.33, 0.135, 0.36), 0.38, (0.38, 0.190, 0.43)),
    (150, None, None, (0.27, 0.130, 0.30), 0.31, (0.31, 0.190, 0.36)),
    (185, None, None, (0.22, 0.130, 0.26), 0.25, (0.25, 0.190, 0.32)),
    (240, None, None, (0.170, 0.130, 0.21), 0.19, (0.195, 0.185, 0.27)),
    (300, None, None, (0.135, 0.125, 0.185), 0.150, (0.155, 0.180, 0.24)),
    (400, None, None, None, 0.115, (0.120, 0.175, 0.21)),
    (500, None, None, None, 0.090, (0.099, 0.170, 0.20)),
    (630, None, None, None, 0.068, (0.079, 0.170, 0.185)),
]

# Flexible cables, non-armoured
cable_data["4F3A"] = {}
# Note that there are derating factors based on temperature.
cable_data["4F3A"]["ratings"] = [
    (0.5, 3, 3, None),
    (0.75, 6, 6, None),
    (1, 10, 10, None),
    (1.25, 13, None, None),
    (1.5, 16, 16, None),
    (2.5, 25, 20, None),
    (4, 32, 25, None),
]

cable_data["4F3A"]["voltage_drop"] = [
    (0.5, None, 93, 80, None, None),
    (0.75, None, 62, 54, None, None),
    (1, None, 46, 40, None, None),
    (1.25, None, 37, None, None, None),
    (1.5, None, 32, 27, None, None),
    (2.5, None, 19, 16, None, None),
    (4, None, 12, 10, None, None),
]


# Eland Cables H07RN-F Cable Datasheet
cable_data["Eland"] = {}
# CSA, Two conductors, 3-5 conductors, separate conductors
cable_data["Eland"]["ratings"] = [
    (2.5, 25, 20, None),
    (4, 41, 36, None),
    (6, 53, 47, None),
    (10, 73, 64, None),
    (16, 99, 86, None),
    (25, 131, 114, None),
    (35, None, 140, 192),
    (50, None, 170, 240),
    (70, None, 216, 297),
    (95, None, 262, 354),
    (120, None, 303, 414),
    (150, None, 348, 476),
    (185, None, 397, 540),
    (240, None, 467, 645),
    (300, None, 537, 741),
    (400, None, None, 885),
    (630, None, None, 1190),
]

cable_data["Eland"]["voltage_drop"] = [
    # 1    2     3               4                       5     6
    (1.5, 32, 32, 27, None, None),
    (2.5, 19, 19, 16, None, None),
    (4, 13, 13, 11.0, None, None),
    (6, 8.4, 8.4, 7.30, None, None),
    (10, 5.0, 5.0, 4.3, None, None),
    (16, 3.1, 3.1, 2.7, None, None),
    (25, 2.0, (2, 0.175, 2), (1.700, 0.150, 1.700), None, None),
    (35, 1.42, None, (1.200, 0.150, 1.200), None, (1.420, 0.210, 1.430)),
    (50, 0.99, None, (0.900, 0.145, 0.910), None, (0.990, 0.210, 1.010)),
    (70, 0.70, None, (0.610, 0.140, 0.630), None, (0.700, 0.200, 0.720)),
    (95, None, None, (0.460, 0.135, 0.480), None, (0.530, 0.195, 0.560)),
    (120, None, None, (0.360, 0.135, 0.390), None, (0.410, 0.190, 0.460)),
    (150, None, None, (0.290, 0.130, 0.320), None, (0.330, 0.190, 0.380)),
    (185, None, None, (0.240, 0.130, 0.270), None, (0.270, 0.190, 0.330)),
    (240, None, None, (0.185, 0.130, 0.220), None, (0.210, 0.185, 0.280)),
    (300, None, None, (0.145, 0.125, 0.195), None, (0.170, 0.180, 0.250)),
    (400, None, None, None, None, (0.130, 0.175, 0.220)),
    (630, None, None, None, None, (0.084, 0.170, 0.190)),
]
