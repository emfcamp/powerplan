from powerplan import Generator
from math import sqrt


def test_zs(plan):
    gen = Generator(name="A", type="135kVA")
    plan.add_node(gen)

    # Arrive at the result by an independent route...
    spec = gen.get_spec()
    Ibase = spec["power"] / (sqrt(3) * spec["voltage"])
    Ifault = (100 / spec["transient_reactance"]) * Ibase
    Z = spec["voltage"] / (sqrt(3) * Ifault)
    assert Z == gen.z_e()
