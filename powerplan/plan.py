import networkx as nx
from networkx.readwrite import json_graph
from .cables import get_cable_config, select_cable_size
from .validator import validate_basic, validate_spec


class Plan(object):
    def __init__(self, spec=None):
        self.graph = nx.DiGraph()
        self.spec = spec

    def add_node(self, node):
        node.plan = self
        self.graph.add_node(node)

    def add_connection(self, from_node, to_node, current, phases=1, distance=None):
        if not self.graph.has_node(from_node):
            self.add_node(from_node)
        if not self.graph.has_node(to_node):
            self.add_node(to_node)

        self.graph.add_edge(from_node, to_node, {'current': current,
                                                 'phases': phases,
                                                 'distance': distance})

    def validate(self):
        errors = validate_basic(self)
        if self.spec:
            errors += validate_spec(self)

        return errors

    def assign_ports(self):
        """ Assign edges a port on each power node. """
        if not self.spec:
            raise Exception("Cannot assign ports with no spec data")

        for a in self.graph.nodes():
            a_spec = a.get_spec()
            for _, b, data in a.outputs():
                if 'in_port' in data:
                    continue

                b_spec = b.get_spec()
                for out_id in range(0, len(a_spec['outputs'])):
                    if out_id in a.outputs_allocated:
                        continue
                    output = a_spec['outputs'][out_id]
                    if data['current'] == output['current'] and \
                            data['phases'] == output['phases']:
                        a.outputs_allocated.add(out_id)
                        break
                else:
                    raise ValueError("Can't assign output from node %s, current %s, phases %s" %
                                     (a, data['current'], data['phases']))

                for in_id in range(0, len(b_spec['inputs'])):
                    if in_id in b.inputs_allocated:
                        continue
                    input = b_spec['inputs'][in_id]
                    if data['current'] == input['current'] and \
                            data['phases'] == input['phases']:
                        b.inputs_allocated.add(in_id)
                        break
                else:
                    raise ValueError("Can't assign input to node %s, current %s, phases %s" %
                                     (b, data['current'], data['phases']))

                if a_spec['outputs'][out_id]['type'] != b_spec['inputs'][in_id]['type']:
                    raise ValueError("Connector types don't match: %s on %s != %s on %s" %
                                     (a_spec['outputs'][out_id]['type'], a,
                                      b_spec['inputs'][in_id]['type'], b))

                self.graph[a][b]['out_port'] = out_id
                self.graph[a][b]['in_port'] = in_id
                self.graph[a][b]['connector'] = a_spec['outputs'][out_id]['type']

    def assign_cables(self, methodology='4F1A'):
        """ Assign cable cross-sectional areas to all connections. """
        for a, b, data in self.graph.edges(data=True):
            config = get_cable_config(data['connector'], data['phases'])
            csa = select_cable_size(data['current'], methodology, config)
            self.graph[a][b]['csa'] = csa
