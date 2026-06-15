import logging
import os.path
from itertools import combinations_with_replacement
from os import walk

import yaml
from pint import PintError

from . import ureg

REQUIRED = ["type", "ref"]


class EquipmentSpec:
    """Stores specification data about power equipment."""

    def __init__(self, metadata_path):
        self.log = logging.getLogger(__name__)
        self.generator = {}
        self.distro = {}
        self.cables = {}
        self.load(metadata_path)

    def __len__(self):
        return len(self.generator)+len(self.distro)+len(self.cables)

    def load(self, metadata_path):
        for dirpath, _dirnames, filenames in walk(metadata_path):
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                path = os.path.join(dirpath, fname)
                if os.path.isfile(path) and ext in (".yml", ".yaml"):
                    _, supplier = os.path.split(dirpath)
                    self.load_file(path, supplier)

    def load_file(self, path, supplier):
        with open(path) as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)

        if not data:
            return
        for item in data:
            self.import_equipment(item, supplier)

    def import_equipment(self, item, supplier):
        if "type" not in item:
            self.log.error("Type required: %s", item)
            return

        self.parse_item(item)
        item["supplier"] = supplier
        if item["type"] == "generator":
            for field in ("voltage", "power", "transient_reactance"):
                if field in item:
                    try:
                        item[field] = ureg(item[field])
                    except PintError as e:
                        raise ValueError(
                            f"Unable to parse {field}: {item[field]} ({e})"
                        ) from e
            self.generator[item["ref"]] = item
        elif item["type"] in ("distro", "amf"):
            self.distro[item["ref"]] = item
        elif item["type"] == "cable":
            item["rating"] = self.convert_current(item["rating"])
            self.cables[(item["connector"], item["rating"], item["phases"])] = item

    def parse_item(self, item):
        for key in ["inputs", "outputs"]:
            res = []
            for io in item.get(key, []):
                io["current"] = self.convert_current(io["current"])
                if "phases" not in io:
                    io["phases"] = 1

                count = 1
                if "count" in io:
                    count = io["count"]
                    del io["count"]

                for _i in range(0, count):
                    res.append(io)
            item[key] = res

    def convert_current(self, val):
        return ureg(val).to(ureg.A).magnitude

    def select_cable(self, connector, rating, phases, length):
        """Select appropriate cables for a run.

        Returns a list of cable lengths and the cross-sectional area of the cable.
        """
        key = (connector, rating, phases)
        if key not in self.cables:
            raise ValueError(
                f"No cable data available for {connector}, {rating}A, {phases} phases"
            )

        if length is None:
            return (None, self.cables[key]["csa"])

        # Calculate the shortest combination of cable lengths.
        # The n-sum problem!

        lengths = sorted(self.cables[key]["lengths"])

        combinations = self.find_cable_combinations(lengths, length)

        selected_lengths = combinations[0][2]  # Get the cable lengths from the best combo


        return (selected_lengths, self.cables[key]["csa"])

    def find_cable_combinations(self, stock, min_length, small_threshold=5.0):
        """
        Finds combinations of up to 5 cables that meet or exceed a minimum length,
        ranking them using weights and a penalty for cables below a threshold.
        """
        if not stock:
            return []

        valid_combinations = []
        max_stock_item = max(stock)

        # weight multipliers
        EXCESS_LENGTH_WEIGHT = 5.0  # Penalty per unit of wasted length
        CABLE_COUNT_WEIGHT = 15.0  # Penalty per cable used (prefers fewer joints)
        THRESHOLD_PENALTY = 15.0  # Penalty per instance of small cables on long runs

        # check combinations from 1 up to 5 cables
        for r in range(1, 6):
            for combo in combinations_with_replacement(stock, r):
                total = sum(combo)

                if total >= min_length:
                    excess = float(total - min_length)
                    num_cables = len(combo)

                    # base penalty for wasting length
                    score = excess * EXCESS_LENGTH_WEIGHT

                    # add penalty for using more cables (prefer fewer joints)
                    score += num_cables * CABLE_COUNT_WEIGHT

                    # disincentivize cables <= threshold ONLY IF target > largest cable
                    if min_length > max_stock_item:
                        # Count how many cables in this combo fall below or equal the threshold
                        small_cable_count = sum(1 for length in combo if length <= small_threshold)
                        score += (small_cable_count * THRESHOLD_PENALTY)

                    valid_combinations.append((score, total, combo))

        # sort by penalty score ascending (lowest score = best option)
        valid_combinations.sort(key=lambda x: x[0])

        if not len(valid_combinations):
            raise ValueError(f"No valid cable combinations found to meet length {min_length}")
            
        return valid_combinations
