import logging
from pint import PintError
import yaml
import os.path
from os import walk
from . import ureg

REQUIRED = ["type", "ref"]


class EquipmentSpec(object):
    """Stores specification data about power equipment."""

    def __init__(self, metadata_path):
        self.log = logging.getLogger(__name__)
        self.generator = {}
        self.distro = {}
        self.cables = {}
        self.load(metadata_path)

    def load(self, metadata_path):
        for (dirpath, dirnames, filenames) in walk(metadata_path):
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                path = os.path.join(dirpath, fname)
                if os.path.isfile(path) and ext in (".yml", ".yaml"):
                    _, supplier = os.path.split(dirpath)
                    self.load_file(path, supplier)

    def load_file(self, path, supplier):
        with open(path, "r") as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)

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
                        raise ValueError(f"Unable to parse {field}: {item[field]} ({e})")
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

                for i in range(0, count):
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
            raise ValueError("No cable data available for %s, %sA, %s phases" % key)

        if length is None:
            return (None, self.cables[key]["csa"])

        # Calculate the shortest combination of cable lengths.
        # The n-sum problem!

        lengths = sorted(self.cables[key]["lengths"])
        selected_lengths = []

        while sum(selected_lengths) <= length:
            # See if the length is satisfied either by a single cable
            # or a pair of adjacent lengths.
            for i in range(len(lengths)):
                if lengths[i] + sum(selected_lengths) >= length:
                    selected_lengths += [lengths[i]]
                    break

                if i > 0 and lengths[i] + lengths[i - 1] >= length:
                    selected_lengths += [lengths[i], lengths[i - 1]]
                    break
            else:
                # It isn't, so add the longest cable to the list and repeat.
                selected_lengths += [lengths[-1]]

        return (selected_lengths, self.cables[key]["csa"])
