import networkx as nx
from . import ureg
from .cables import CableConfiguration, get_cable_ratings
from .data import Generator, Distro, VirtualNode
from .validator import validate_basic, validate_spec


class Plan(object):
    def __init__(self, name=None, parent=None, spec=None, methodology='4F1A', graph=None):
        self.name = name
        self.parent = parent

        if graph:
            self.graph = graph
        else:
            self.graph = nx.DiGraph()
        self.spec = spec
        self.methodology = methodology

    def num_generators(self):
        return sum(1 for n in self.graph.nodes() if type(n) == Generator)

    def num_distros(self):
        return sum(1 for n in self.graph.nodes() if type(n) == Distro)

    def add_node(self, node):
        node.plan = self
        self.graph.add_node(node)

    def add_connection(self, from_node, to_node, current=None, phases=1, length=None):
        if not self.graph.has_node(from_node):
            self.add_node(from_node)
        if not self.graph.has_node(to_node):
            self.add_node(to_node)

        self.graph.add_edge(from_node, to_node, current=current,
                            phases=phases, length=length)

    def validate(self):
        errors = validate_basic(self)
        if self.spec:
            errors += validate_spec(self)

        return errors

    def nodes(self, include_virtual=False, data=False):
        """ Enumerate nodes in the plan.
            Excludes virtual nodes (loads) unless `include_virtual` is True.
        """
        for node, node_data in self.graph.nodes(True):
            if not include_virtual and isinstance(node, VirtualNode):
                continue

            if data:
                yield (node, node_data)
            else:
                yield node

    def edges(self, include_virtual=False, data=False):
        for u, v, edge_data in self.graph.edges(data=True):
            if not include_virtual and (isinstance(u, VirtualNode) or isinstance(v, VirtualNode)):
                continue

            if data:
                yield (u, v, edge_data)
            else:
                yield (u, v)

    def generate(self):
        self.assign_ports()
        self.assign_cables()
        self.calculate_voltage_drop()

    def assign_output(self, node, current, phases):
        spec = node.get_spec()
        outputs = spec.get('outputs', [])

        for out_id in range(0, len(outputs)):
            if out_id in node.outputs_allocated:
                continue
            output = spec['outputs'][out_id]
            if current == output['current'] and \
                    phases == output['phases']:
                node.outputs_allocated.add(out_id)
                return out_id
        else:
            raise ValueError("Can't assign output from node %s, current %s, phases %s" %
                             (node, current, phases))

    def assign_input(self, node, current, phases):
        spec = node.get_spec()
        inputs = spec.get('inputs', [])

        for in_id in range(0, len(inputs)):
            if in_id in node.inputs_allocated:
                continue
            input = spec['inputs'][in_id]
            if current == input['current'] and \
                    phases == input['phases']:
                node.inputs_allocated.add(in_id)
                return in_id
        else:
            raise ValueError("Can't assign input to node %s, current %s, phases %s" %
                             (node, current, phases))

    def assign_ports(self):
        """ Assign edges a port on each power node.

            If a node at either end of a cable doesn't have a spec
            (perhaps because it has no type assigned), it will be skipped.
        """
        if not self.spec:
            raise Exception("Cannot assign ports with no spec data")

        for a in self.nodes():
            a_spec = a.get_spec()

            if a_spec is None:
                continue

            for b, data in a.outputs():
                if 'in_port' in data:
                    continue

                b_spec = b.get_spec()
                if b_spec is None:
                    continue

                out_id = self.assign_output(a, data['current'], data['phases'])
                in_id = self.assign_input(b, data['current'], data['phases'])

                if a_spec['outputs'][out_id]['type'] != b_spec['inputs'][in_id]['type']:
                    raise ValueError("Connector types don't match: %s on %s != %s on %s" %
                                     (a_spec['outputs'][out_id]['type'], a,
                                      b_spec['inputs'][in_id]['type'], b))

                self.graph[a][b]['out_port'] = out_id
                self.graph[a][b]['in_port'] = in_id
                self.graph[a][b]['connector'] = a_spec['outputs'][out_id]['type']

    def assign_cables(self):
        """ Assign cable cross-sectional areas to all cables.

            Cables with no assigned connectors will be skipped.
        """
        for a, b, data in self.edges(data=True):
            if 'connector' not in data:
                continue

            lengths, csa = self.spec.select_cable(data['connector'], data['current'],
                                                  data['phases'], data['length'])
            self.graph[a][b]['csa'] = csa
            self.graph[a][b]['cable_lengths'] = lengths

            if data['connector'] == 'Powerlock':
                config = CableConfiguration.TWO_SINGLE
            elif data['connector'] == 'IEC 60309':
                config = CableConfiguration.MULTI_CORE
            else:
                raise ValueError("Unknown cable configuration: %s", data['connector'])

            ratings = get_cable_ratings(csa, self.methodology, config)
            drop = ratings['voltage_drop']
            if type(drop) == tuple:
                # Use the scalar impedance value (Zr)
                # TODO: use the complex impedance and calculate with expected PF
                drop = drop[2]

            if drop is None:
                continue

            drop *= ureg('mohm/m')

            self.graph[a][b]['impedance'] = drop

    def calculate_voltage_drop(self):
        " Calculate voltage drop per cable length. "
        for a, b, data in self.edges(data=True):
            if not data.get('cable_lengths') or not data.get('impedance'):
                continue

            length = sum(data['cable_lengths']) * ureg.m
            source = list(b.sources())[0]
            # Per-phase current is the load in watts divided by the source L-L voltage
            current = b.load() / source.voltage
            self.graph[a][b]['voltage_drop'] = (current * data['impedance'] * length).to(ureg.V)

    def grids(self):
        grids = []
        for c in nx.weakly_connected_components(self.graph):
            generators = [node for node in c if type(node) == Generator]
            if len(generators) == 0:
                continue
            name = generators[0].name
            grids.append(Plan(parent=self, name=name, graph=self.graph.subgraph(c)))

        return sorted(grids, key=lambda plan: plan.name)

    def __repr__(self):
        return "<Plan '{}': {} generators, {} distros, {} connections>".format(
            self.name, self.num_generators(), self.num_distros(), len(self.graph.edges()))
