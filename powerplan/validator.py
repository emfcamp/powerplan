from .data import Distro, PowerSource


class ValidationError(object):
    def __init__(self, node, description):
        self.node = node
        self.description = description

    def __str__(self):
        return "ValidationError: %s: %s" % (self.description, self.node)

    def __repr__(self):
        return str(self)


def validate_basic(plan):
    errors = []
    for node in plan.graph.nodes():
        in_edges = node.inputs()
        out_edges = node.outputs()

        if isinstance(node, PowerSource):
            if len(out_edges) == 0:
                errors.append(ValidationError(node, "Generator has no outgoing connections"))
            if len(in_edges) > 0:
                errors.append(ValidationError(node, "Generator has incoming connections"))

        elif type(node) == Distro:
            if len(in_edges) == 0:
                errors.append(ValidationError(node, "Distro has no incoming connections"))

    return errors


def validate_spec(plan):
    errors = []

    for node in plan.graph.nodes():
        if node.type is None:
            errors.append(ValidationError(node, "Node has no type"))
            continue

        spec = node.get_spec()
        if spec is None:
            errors.append(ValidationError(node, "Spec not found: %s" % node.type))
            continue

        if len(node.outputs()) > len(spec.get('outputs', [])):
            errors.append(ValidationError(node, "More outputs than available"))
            continue

        if len(node.inputs()) > len(spec.get('inputs', [])):
            errors.append(ValidationError(node, "More inputs than available"))
            continue

        for _, _, attribs in node.outputs():
            for item in spec['outputs']:
                if item['phases'] == attribs['phases'] and item['current'] == attribs['current']:
                    break
            else:
                errors.append(ValidationError(node, "No output for current: %s, phases: %s" %
                                              (attribs['current'], attribs['phases'])))

        for _, _, attribs in node.inputs():
            for item in spec['inputs']:
                if item['phases'] == attribs['phases'] and item['current'] == attribs['current']:
                    break
            else:
                errors.append(ValidationError(node, "No input for current: %s, phases: %s" %
                                              (attribs['current'], attribs['phases'])))

    return errors
