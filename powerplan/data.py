from typing import Optional, Any, Iterable, Tuple, Set  # noqa
from math import sqrt
from . import ureg


class PowerNode(object):
    def __init__(self,
                 name: Optional[str]=None,
                 type: Optional[str]=None,
                 id: Optional[Any]=None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.plan = None
        self.inputs_allocated = set()
        self.outputs_allocated = set()

    def __repr__(self) -> str:
        if self.name:
            return "%s(name=%s)" % (self.__class__.__name__, self.name)
        elif self.id:
            return "%s(id=%s)" % (self.__class__.__name__, self.id)
        else:
            return "%s(%s)" % (self.__class__.__name__, id(self))

    def inputs(self, include_virtual: bool=False) -> Iterable[Tuple['PowerNode', Any]]:
        if self.plan is None:
            raise Exception("Node is not associated with a plan")
        for node, _, data in self.plan.graph.in_edges([self], data=True):
            if not include_virtual and isinstance(node, VirtualNode):
                continue
            yield (node, data)

    def outputs(self, include_virtual: bool=False) -> Iterable[Tuple['PowerNode', Any]]:
        if self.plan is None:
            raise Exception("Node is not associated with a plan")
        for _, node, data in self.plan.graph.out_edges([self], data=True):
            if not include_virtual and isinstance(node, VirtualNode):
                continue
            yield (node, data)

    def load(self) -> float:
        s = sum(node.load() for node, _ in self.outputs(True))
        if s == 0:
            s *= ureg.W
        return s

    def source(self, ipt: Optional['PowerNode']=None) -> 'PowerNode':
        """ Return the power source for this node.

            If the node has multiple inputs you must specify which upstream node to
            look via.
        """
        if ipt is None:
            inputs = list(self.inputs())
            if len(inputs) > 1:
                raise Exception("Node %s: more than one input - source needs specifying." % self)
            return self.source_for_input(inputs[0][0])
        else:
            return self.source_for_input(ipt)

    def source_for_input(self, ipt: 'PowerNode') -> 'PowerNode':
        if isinstance(ipt, PowerSource):
            return ipt
        else:
            return ipt.source()

    @property
    def voltage(self):
        " Nominal voltage L-L"
        voltages = set(ipt.voltage.magnitude for ipt, _ in self.inputs())
        if len(voltages) > 1:
            raise Exception("Nominal voltages differ between sources: {}".format(voltages))
        return list(voltages)[0] * ureg.V

    @property
    def voltage_ln(self) -> int:
        " Nominal Voltage L-N "
        return self.voltage / sqrt(3)

    def z_e(self):
        return max(ipt.z_e() for ipt, _ in self.inputs())

    def i_pf(self, direction=None):
        " Prospective fault current for a L-N or L-E fault (amps). "
        I = self.voltage_ln / self.z_s()
        return I.to(ureg.A)

    def i_n(self):
        "Nominal breaker current at the input of this node"
        input_port = list(self.inputs())[0][1]
        if 'rating' in input_port:
            rating = input_port['rating']
        else:
            rating = input_port['current']
        return rating * ureg('A')

    def v_drop_ratio(self, direction=None):
        " Voltage drop L-N as a ratio of source voltage "
        v_drop = self.v_drop(direction)

        if v_drop is None:
            return None
        return (v_drop / self.voltage_ln).magnitude


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
        return self.get_spec().get('voltage')

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

    def _input_attrs(self, source):
        if source is None:
            inputs = list(self.inputs())
            if len(inputs) > 1:
                raise Exception("Node %s: more than one input!" % self)
            return inputs[0]

        for ipt, attrs in self.inputs():
            if ipt == source:
                return ipt, attrs

    def r1(self, direction=None):
        """ The phase conductor impedance from the power source to this node, in ohms. """
        ipt, attrs = self._input_attrs(direction)

        if not attrs.get('impedance') or not attrs.get('cable_lengths'):
            return None

        # Voltage drop is quoted as r1 + r2 in mV/A/m (milliohms/m) although unit conversion
        # is handled by pint. We need to divide by2 to get single-leg ohms/m, then multiply
        # by cable length
        length = sum(attrs['cable_lengths']) * ureg.m
        Z = length * (attrs['impedance'] / 2) + ipt.r1()
        return Z

    def z_s(self, direction=None):
        " Earth fault loop impedance (ohms)"
        z_e = self.z_e()
        if z_e is None:
            return None
        r1 = self.r1(direction)
        if r1 is None:
            return None
        return z_e + (r1 * 2)

    def v_drop(self, direction=None):
        " Voltage drop L-N (volts)"
        ipt, attrs = self._input_attrs(direction)
        if attrs.get('voltage_drop') is None:
            return None

        v_drop = ipt.v_drop()
        if v_drop is None:
            return None
        return v_drop + attrs['voltage_drop']

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


class AMF(Distro):
    """ Automatic Mains Failure panel.

        This has two inputs and switches between them if the supply fails.
    """

    def r1(self, source=None):
        " Return the highest R1 from each input "
        if source is not None:
            return super().r1(source)
        else:
            return max(self.r1(source) for source, _ in self.inputs())

    def z_s(self, source=None):
        " Return the highest Zs from each input "
        if source is not None:
            return super().z_s(source)
        else:
            return max(self.z_s(source) for source, _ in self.inputs())

    def i_pf(self, source=None):
        """ Return the *lowest* prospective fault current for each input.

            NOTE: if this location is at risk of prospective fault currents
            exceeding breaking capacity, the maximum will also need considering.
            This situation is not plausible in generator-fed temporary installations.
        """
        if source is not None:
            return super().i_pf(source)
        else:
            return min(self.i_pf(source) for source, _ in self.inputs())

    def v_drop(self, source=None):
        " Voltage drop L-N (volts)"
        if source is not None:
            return super().v_drop(source)
        else:
            v_drops = [self.v_drop(source) for source, _ in self.inputs()]
            if any(v_drop is None for v_drop in v_drops):
                return None
            return max(v_drops)


class LogicalSource(PowerSource):
    """ A power source which represents the input from another section
        of the plan, used to preserve independent grids when an AMF joins
        them.

        This source replicates the voltage drop and impedance from its
        position in the upstream grid.
    """

    def __init__(self, name, voltage, v_drop, z_s,
                 current, phases):
        self.name = name
        self.id = None
        self.type = "Link"
        self._voltage = voltage
        self._v_drop = v_drop
        self._z_s = z_s
        self.spec = {
            'outputs': [{
                'current': current,
                'phases': phases
            }],
            'inputs': []
        }

    def get_spec(self):
        return self.spec

    def v_drop(self, _=None):
        return self._v_drop

    @property
    def voltage(self):
        return self._voltage

    def z_s(self):
        return self._z_s

    def i_n(self):
        return self.spec['outputs'][0]['current'] * ureg.A


class LogicalSink(PowerNode):
    """ A power sink which represents the output to another section of
        the plan.

        This sink replicates the load from the downstream grid.
    """

    def __init__(self, name, load, current, phases):
        self.name = name
        self.id = None
        self.type = "Link"
        self._load = load
        self.spec = {
            'inputs': [{
                'current': current,
                'phases': phases
            }],
            'outputs': []
        }

    def get_spec(self):
        return self.spec
