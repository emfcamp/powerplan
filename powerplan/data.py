

class PowerNode(object):
    def __init__(self, name=None, type=None, id=None):
        self.name = name
        self.type = type
        self.id = id
        self.plan = None
        self.inputs_allocated = set()
        self.outputs_allocated = set()

    def __repr__(self):
        if self.name:
            return "%s(name=%s)" % (self.__class__.__name__, self.name)
        elif self.id:
            return "%s(id=%s)" % (self.__class__.__name__, self.id)
        else:
            return "%s(%s)" % (self.__class__.__name__, id(self))

    def inputs(self):
        return self.plan.graph.in_edges([self], data=True)

    def outputs(self):
        return self.plan.graph.out_edges([self], data=True)


class PowerSource(PowerNode):
    pass


class Generator(PowerSource):
    def get_spec(self):
        return self.plan.spec.generator.get(self.type)


class Distro(PowerNode):
    def get_spec(self):
        return self.plan.spec.distro.get(self.type)


class PowerLoad(PowerNode):
    def __init__(self, name, load):
        self.name = name
        self.load = load
