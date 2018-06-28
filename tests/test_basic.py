from powerplan import Plan, Generator, Distro


def test_create_graph():
    plan = Plan()
    gen = Generator(name="A")
    dist = Distro(name="A1")
    plan.add_node(gen)
    plan.add_connection(gen, dist, 400, 3)

    assert plan.graph.number_of_nodes() == 2
    assert plan.graph.number_of_edges() == 1
    assert len(plan.validate()) == 0
    assert plan.num_generators() == 1
    assert plan.num_distros() == 1


def test_failed_validation():
    plan = Plan()
    dist = Distro(name="A1")
    plan.add_node(dist)

    assert len(plan.validate()) == 1


def test_spec(spec, plan):
    assert len(spec.generator) == 1
    assert len(spec.distro) == 23

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


def test_port_assignment(plan):
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
    assert a4.source() == gen


def test_subgraph(plan):
    a = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(a, a1, 400, 3, length=10)

    b = Generator(name="B", type="135kVA")
    b1 = Distro(name="B1", type="SPEC-7")
    plan.add_connection(b, b1, 400, 3, length=10)
    plan.generate()

    grids = list(plan.grids())

    assert len(grids) == 2

    for grid in grids:
        assert grid.parent == plan


def test_select_cable_lengths(spec):
    assert spec.select_cable('IEC 60309', 63, 3, 34)[0] == [25, 10]
    assert spec.select_cable('IEC 60309', 63, 3, 41)[0] == [50]
    assert spec.select_cable('IEC 60309', 63, 3, 62)[0] == [50, 25]


def test_fault_current(plan):
    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3, length=10)

    a2 = Distro(name="A2", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3, length=52)

    a3 = Distro(name="A3", type="EPS/63-3")
    plan.add_connection(a1, a3, 63, 3, length=54)

    a4 = Distro(name="A4", type="TOB-32")
    plan.add_connection(a3, a4, 32, 1, length=25)

    assert len(plan.validate()) == 0
    plan.generate()

    a4.i_pf()


def test_duplicate_node_name(plan):
    gen = Generator(name="A", type="135kVA")
    a1 = Distro(name="A1", type="SPEC-7")
    plan.add_connection(gen, a1, 400, 3)

    a2 = Distro(name="A1", type="EPS/63-4")
    plan.add_connection(a1, a2, 63, 3)

    assert len(plan.validate()) == 2
