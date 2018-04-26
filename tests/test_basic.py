from powerplan import Plan, EquipmentSpec
from powerplan.data import Generator, Distro
import os.path

thispath = os.path.realpath(os.path.dirname(__file__))


def test_create_graph():
    gen = Generator(name="A")
    dist = Distro(name="A1")
    plan = Plan()
    plan.add_node(gen)
    plan.add_connection(gen, dist, 400, 3)

    assert plan.graph.number_of_nodes() == 2
    assert plan.graph.number_of_edges() == 1
    assert len(plan.validate()) == 0


def test_failed_validation():
    dist = Distro(name="A1")
    plan = Plan()
    plan.add_node(dist)

    assert len(plan.validate()) == 1


def test_spec():
    spec = EquipmentSpec(os.path.join(thispath, './fixtures'))

    assert len(spec.generator) == 1
    assert len(spec.distro) == 21

    plan = Plan(spec)

    gen = Generator(name="A", type="135kVA")
    dist = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, dist, 400, 3)
    assert len(plan.validate()) == 0

    # Add another distro connected to a generator with only one output
    dist2 = Distro(name="A2", type="SPEC-7")
    plan.add_connection(gen, dist2, 400, 3)
    assert len(plan.validate()) == 1

    # Add a distro connected with an incorrect cable rating
    dist3 = Distro(name="A3", type="EPS/32")
    plan.add_connection(dist, dist3, 32, 3)
    assert len(plan.validate()) == 2


def test_port_assignment():
    spec = EquipmentSpec(os.path.join(thispath, './fixtures'))
    plan = Plan(spec)

    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3)

    a2 = Distro(name="A2", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3)

    a3 = Distro(name="A3", type="EPS/63-3")
    plan.add_connection(a1, a3, 63, 3)

    a4 = Distro(name="A4", type="TOB-32")
    plan.add_connection(a3, a4, 32, 1)

    assert len(plan.validate()) == 0
    plan.assign_ports()
    assert plan.graph[a1][a2]['out_port'] == 0
    assert plan.graph[a1][a2]['in_port'] == 0
    assert plan.graph[a1][a3]['out_port'] == 1
    assert plan.graph[a1][a3]['in_port'] == 0

    plan.assign_cables()

    assert plan.graph[a1][a2]['csa'] == 16
