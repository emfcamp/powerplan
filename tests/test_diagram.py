from powerplan import Plan
from powerplan.data import Distro, Generator, Load
from powerplan.diagram import to_dot


def test_create_graph(spec):
    plan = Plan(name="Test", spec=spec)

    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3)

    a2 = Distro(name="A2", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3)

    a3 = Distro(name="A3", type="EPS/63-3")
    plan.add_connection(a1, a3, 63, 3)

    a4 = Distro(name="A4", type="TOB-32")
    plan.add_connection(a3, a4, 32, 1)

    a4_load = Load(name="A4 Load", load=1000)
    plan.add_connection(a4, a4_load)

    assert len(plan.validate()) == 0
    plan.generate()

    dot = to_dot(plan)
    dot.to_string()
    dot.create_pdf()


def test_graph_incomplete_spec(spec):
    plan = Plan(name="Test", spec=spec)

    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3)

    a2 = Distro(name="A2", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3)

    a3 = Distro(name="A3")
    plan.add_connection(a1, a3, 63, 3)

    a4 = Distro(name="A4", type="TOB-32")
    plan.add_connection(a3, a4, 32, 1)

    plan.generate()

    dot = to_dot(plan)
    dot.to_string()
    dot.create_pdf()
