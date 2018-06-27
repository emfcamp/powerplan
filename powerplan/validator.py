import networkx as nx
from .data import Distro, PowerSource


class ValidationError(object):
    def __init__(self, node, description):
        self.node = node
        self.description = description

    def __str__(self):
        return "[{} {}] {}".format(self.node, self.node.type, self.description)

    def __repr__(self):
        return str(self)


def validate_basic(plan):
    errors = []
    for node in plan.nodes():
        in_edges = list(node.inputs())
        out_edges = list(node.outputs())

        if isinstance(node, PowerSource):
            if len(out_edges) == 0:
                errors.append(ValidationError(node, "Generator has no outgoing connections"))
            if len(in_edges) > 0:
                errors.append(ValidationError(node, "Generator has incoming connections"))

        elif type(node) == Distro:
            if len(in_edges) == 0:
                errors.append(ValidationError(node, "Distro has no incoming connections"))

    #for c in nx.weakly_connected_components(plan.graph):
    #    sources = [node for node in c if isinstance(node, PowerSource)]
    #    if len(sources) == 0:
    #        errors.append(ValidationError(c[0], "Unconnected grid: {}".format(", ".join(str(n) for n in c))))

    return errors


def validate_spec(plan):
    errors = []

    for node in plan.nodes():
        if node.type is None:
            errors.append(ValidationError(node, "Node has no type"))
            continue

        spec = node.get_spec()
        if spec is None:
            errors.append(ValidationError(node, "Spec not found for item: %s" % node.type))
            continue

        if len(list(node.outputs())) > len(spec.get('outputs', [])):
            errors.append(ValidationError(node, "More outputs than available"))
            continue

        if len(list(node.inputs())) > len(spec.get('inputs', [])):
            errors.append(ValidationError(node, "More inputs than available: %s" % (node.inputs(), )))
            continue

        for _, attribs in node.outputs():
            for item in spec['outputs']:
                if item['phases'] == attribs['phases'] and item['current'] == attribs['current']:
                    break
            else:
                errors.append(ValidationError(node, "No output for current: %s, phases: %s" %
                                              (attribs['current'], attribs['phases'])))

        for _, attribs in node.inputs():
            for item in spec['inputs']:
                if item['phases'] == attribs['phases'] and item['current'] == attribs['current']:
                    break
            else:
                errors.append(ValidationError(node, "No input for current: %s, phases: %s" %
                                              (attribs['current'], attribs['phases'])))

    return errors
