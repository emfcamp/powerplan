import logging
import yaml
import os.path
import pint
from os import walk

REQUIRED = ['type', 'ref']

ureg = pint.UnitRegistry()


class EquipmentSpec(object):
    """ Stores specification data about power equipment. """

    def __init__(self, metadata_path):
        self.log = logging.getLogger(__name__)
        self.generator = {}
        self.distro = {}
        self.load(metadata_path)

    def load(self, metadata_path):
        for (dirpath, dirnames, filenames) in walk(metadata_path):
            for fname in filenames:
                _, ext = os.path.splitext(fname)
                path = os.path.join(dirpath, fname)
                if os.path.isfile(path) and ext in ('.yml', '.yaml'):
                    self.load_file(path)

    def load_file(self, path):
        with open(path, 'r') as f:
            data = yaml.load(f)

        for item in data:
            self.import_equipment(item)

    def import_equipment(self, item):
        if 'type' not in item:
            self.log.error("Type required: %s", item)
            return

        self.parse_item(item)
        if item['type'] == 'generator':
            self.generator[item['ref']] = item
        elif item['type'] == 'distro':
            self.distro[item['ref']] = item

    def parse_item(self, item):
        for key in ['inputs', 'outputs']:
            res = []
            for io in item.get(key, []):
                io['current'] = self.convert_current(io['current'])
                if 'phases' not in io:
                    io['phases'] = 1

                count = 1
                if 'count' in io:
                    count = io['count']
                    del io['count']

                for i in range(0, count):
                    res.append(io)
            item[key] = res

    def convert_current(self, val):
        return ureg(val).to(ureg.A).magnitude
