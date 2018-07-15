from powerplan import Generator, Distro
from powerplan.bom import generate_bom_html


def test_graph_incomplete_spec(plan):
    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3, length=10)

    a2 = Distro(name="A2", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3, length=52)

    a3 = Distro(name="A3", type="EPS/63-3")
    plan.add_connection(a1, a3, 63, 3, length=54)

    a4 = Distro(name="A4", type="TOB-32")
    plan.add_connection(a3, a4, 32, 1, length=25)

    plan.generate()

    assert len(generate_bom_html(plan)) > 0
