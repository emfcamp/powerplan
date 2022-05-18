from powerplan import Generator, ureg
from math import sqrt


def test_zs(plan):
    gen = Generator(name="A", type="135kVA")
    plan.add_node(gen)

    # Arrive at the result by an independent route...
    spec = gen.get_spec()
    Ibase = spec["power"] / (sqrt(3) * spec["voltage"])
    Ifault = Ibase / spec["transient_reactance"]
    Z = (spec["voltage"] / (sqrt(3) * Ifault)).to(ureg.ohm)
    assert round(Z, 5) == round(gen.z_e(), 5)
