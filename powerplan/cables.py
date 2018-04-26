from enum import Enum
from .cable_data import cable_data


class CableConfiguration(Enum):
    TWO_CORE = 1    # two-core cable, with or without protective conductor
    MULTI_CORE = 2  # multi-phase three-core, four-core, or five-core cable
    TWO_SINGLE = 3  # two single-core cables, laid touching


def select_cable_size(current, methodology, configuration):
    """ Return the cross sectional area for a cable at the
        provided current. """
    ratings = cable_data[methodology]['ratings']
    col = configuration.value

    for row in ratings:
        if row[col] is not None and row[col] >= current:
            return row[0]
    return None


def get_cable_ratings(csa, methodology, configuration):
    data = cable_data[methodology]

    voltage_drop = None
    rating = None
    for row in data['ratings']:
        if csa == row[0]:
            rating = row[configuration.value]

    if configuration == CableConfiguration.TWO_CORE:
        col = 2  # Two-core cable, single phase AC
    elif configuration == CableConfiguration.MULTI_CORE:
        col = 3
    elif configuration == CableConfiguration.TWO_SINGLE:
        col = 5  # Two single-core cables, touching, 1ph AC

    for row in data['voltage_drop']:
        if csa == row[0]:
            voltage_drop = row[col]

    return {'rating': rating, 'voltage_drop': voltage_drop}


def get_cable_config(connector, phases):
    """ Given a connector name, return the appropriate cable configuration.
        This is kind of ugly. """

    if connector.lower() == 'powerlock':
        return CableConfiguration.TWO_SINGLE
    elif connector.lower() == 'iec 60309' and phases == 3:
        return CableConfiguration.MULTI_CORE
    elif connector.lower() == 'iec 60309' and phases == 1:
        return CableConfiguration.TWO_CORE
    else:
        raise ValueError("Can't guess cable configuration for connector: %s, phases: %s" %
                         (connector, phases))
