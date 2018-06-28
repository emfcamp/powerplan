from . import ureg
from math import sqrt


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

    def inputs(self, include_virtual=False):
        for node, _, data in self.plan.graph.in_edges([self], data=True):
            if not include_virtual and isinstance(node, VirtualNode):
                continue
            yield (node, data)

    def outputs(self, include_virtual=False):
        for _, node, data in self.plan.graph.out_edges([self], data=True):
            if not include_virtual and isinstance(node, VirtualNode):
                continue
            yield (node, data)

    def load(self):
        s = sum(node.load() for node, _ in self.outputs(True))
        if s == 0:
            s *= ureg.W
        return s


class PowerSource(PowerNode):
    def r1(self):
        return 0 * ureg.ohm

    def v_drop(self):
        return 0 * ureg.V


class VirtualNode(PowerNode):
    pass


class Generator(PowerSource):
    def get_spec(self):
        return self.plan.spec.generator.get(self.type)

    @property
    def voltage(self):
        " Voltage L-L "
        return self.get_spec().get('voltage')

    @property
    def voltage_ln(self):
        " Voltage L-N "
        return self.get_spec().get('voltage') / sqrt(3)

    @property
    def power(self):
        return self.get_spec().get('power')

    def z_e(self):
        """ Ze (source impedance) of the generator for fault current calculation.

            This is calculated using the transient reactance of the generator.

            Zf: Transient reactance (as per-unit ratio 0-1)
            V:  L-L Voltage (V)
            S:  Generator power (VA)

            Zs = (V**2 * Zf) / S
        """

        spec = self.get_spec()
        voltage = spec.get('voltage')
        power = spec.get('power')
        transient_reactance = spec.get('transient_reactance')

        z = (voltage ** 2 * transient_reactance) / (power * 100)
        return (z).to(ureg.ohm)


class Distro(PowerNode):

    def r1(self):
        """ The phase conductor impedance from the power source to this node, in ohms. """
        inputs = list(self.inputs())
        if len(inputs) > 1:
            raise Exception("Node %s: more than one input calculating r1+r2" % self)

        source, attrs = list(inputs)[0]

        if not attrs.get('impedance') or not attrs.get('cable_lengths'):
            return None

        # Voltage drop is quoted as r1 + r2 in mV/A/m (milliohms/m) although unit conversion
        # is handled by pint. We need to divide by2 to get single-leg ohms/m, then multiply
        # by cable length
        length = sum(attrs['cable_lengths']) * ureg.m
        Z = length * (attrs['impedance'] / 2) + source.r1()
        return Z

    def sources(self):
        for i, _ in self.inputs():
            if isinstance(i, PowerSource):
                yield i
            else:
                yield from i.sources()

    def z_s(self):
        " Earth fault loop impedance (ohms)"
        source = list(self.sources())[0]
        z_e = source.z_e()
        if z_e is None:
            return None
        r1 = self.r1()
        if r1 is None:
            return None
        return z_e + (r1 * 2)

    def i_pf(self):
        " Prospective fault current for a L-N or L-E fault (amps). "
        source = list(self.sources())[0]
        I = source.voltage / (self.z_s() * sqrt(3))
        return I.to(ureg.A)

    def v_drop(self):
        " Voltage drop L-N (volts)"
        inputs = list(self.inputs())
        if len(inputs) > 1:
            raise Exception("Node %s: more than one input calculating v_drop" % self)

        source, attrs = list(inputs)[0]

        if not attrs.get('voltage_drop'):
            return None

        return source.v_drop() + attrs['voltage_drop']

    def v_drop_ratio(self):
        " Voltage drop L-N as a ratio of source voltage "
        v_drop = self.v_drop()
        if v_drop is None:
            return None
        source = list(self.sources())[0]
        return (v_drop / source.voltage_ln).magnitude

    def get_spec(self):
        return self.plan.spec.distro.get(self.type)


class Load(VirtualNode):
    def __init__(self, name, load):
        self.name = name
        self.load_value = load

    def load(self):
        l = ureg.Quantity(str(self.load_value))
        if l.dimensionless:
            l *= ureg.W
        return l
