from powerplan.data import Generator, Distro, Load


def test_load(plan):
    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3, length=10)

    a2 = Distro(name="A2", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3, length=52)

    a3 = Distro(name="A3", type="EPS/63-3")
    plan.add_connection(a1, a3, 63, 3, length=54)

    a4 = Distro(name="A4", type="TOB-32")
    plan.add_connection(a3, a4, 32, 1, length=25)

    a4_load = Load(name="A4 Load", load=1000)
    plan.add_connection(a4, a4_load)

    assert len(plan.validate()) == 0
    plan.generate()

    assert a4_load.load().magnitude == 1000
    assert a4.load().magnitude == 1000
    assert a3.load().magnitude == 1000
    assert a1.load().magnitude == 1000

    a4.v_drop()
