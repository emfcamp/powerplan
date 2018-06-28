from powerplan.data import Generator, Distro, AMF
from powerplan.diagram import to_dot


def test_amf(plan):
    gen_a = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-4")
    plan.add_connection(gen_a, a1, 400, 3, length=10)

    gen_b = Generator(name="B", type="135kVA")
    b1 = Distro(name="B1", type="SPEC-4")
    plan.add_connection(gen_b, b1, 400, 3, length=10)

    amf = AMF(name="AMF-1", type="125AMF-EVENT")
    plan.add_connection(a1, amf, 125, 3, length=10)
    plan.add_connection(b1, amf, 125, 3, length=50)

    ab1 = Distro(name="AB1", type="EPS/63-3")
    plan.add_connection(amf, ab1, 63, 3, length=25)

    assert len(plan.validate()) == 0
    plan.generate()

    grids = plan.grids()
    # We should now have 3 grids - two main grids and a
    # separate logical grid for the AMF.
    assert len(grids) == 3

    dot = to_dot(plan)
    dot.create_pdf()
