import os.path

import pytest

from powerplan import EquipmentSpec, Plan

thispath = os.path.realpath(os.path.dirname(__file__))


@pytest.fixture()
def spec():
    return EquipmentSpec(os.path.join(thispath, "./fixtures"))


@pytest.fixture()
def plan(spec):
    return Plan(spec=spec)
