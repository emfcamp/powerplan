from __future__ import annotations

from typing import TYPE_CHECKING

from .data import Distro, PowerSource

if TYPE_CHECKING:
    from .plan import Plan


class ValidationError:
    def __init__(self, node, description):
        self.node = node
        self.description = description

    def __str__(self):
        return f"[{self.node} {self.node.type}] {self.description}"

    def __repr__(self):
        return str(self)


def validate_node_uniqueness(plan: Plan):
    nodes = sorted(plan.nodes(), key=lambda node: node.name or "")
    duplicates = set()
    for i in range(len(nodes) - 1):
        if nodes[i].name == nodes[i + 1].name:
            duplicates.add(nodes[i])
            duplicates.add(nodes[i + 1])

    return [ValidationError(node, "Duplicate node name") for node in duplicates]


def validate_basic(plan: Plan):
    errors = []
    for node in plan.nodes():
        in_edges = list(node.inputs())
        out_edges = list(node.outputs())

        if isinstance(node, PowerSource):
            if len(out_edges) == 0:
                errors.append(
                    ValidationError(node, "Generator has no outgoing connections")
                )
            if len(in_edges) > 0:
                errors.append(
                    ValidationError(node, "Generator has incoming connections")
                )

        elif type(node) == Distro:
            if len(in_edges) == 0:
                errors.append(
                    ValidationError(node, "Distro has no incoming connections")
                )

    errors += validate_node_uniqueness(plan)
    return errors


def validate_spec(plan: Plan):
    errors = []

    for node in plan.nodes():
        if node.type is None:
            errors.append(ValidationError(node, "Node has no type"))
            continue

        spec = node.get_spec()
        if spec is None:
            errors.append(
                ValidationError(node, "Spec not found for item: %s" % node.type)
            )
            continue

        if len(list(node.outputs())) > len(spec.get("outputs", [])):
            errors.append(ValidationError(node, "More outputs than available"))
            continue

        if len(list(node.inputs())) > len(spec.get("inputs", [])):
            errors.append(
                ValidationError(
                    node, f"More inputs than available: {list(node.inputs())}"
                )
            )
            continue

        for _, attribs in node.outputs():
            for item in spec["outputs"]:
                if (
                    item["phases"] == attribs["phases"]
                    and item["current"] == attribs["current"]
                ):
                    break
            else:
                errors.append(
                    ValidationError(
                        node,
                        f"No output for current: {attribs['current']}, phases: {attribs['phases']}",
                    )
                )

        for _, attribs in node.inputs():
            for item in spec["inputs"]:
                if (
                    item["phases"] == attribs["phases"]
                    and item["current"] == attribs["current"]
                ):
                    break
            else:
                errors.append(
                    ValidationError(
                        node,
                        f"No input for current: {attribs['current']}, phases: {attribs['phases']}",
                    )
                )

    return errors
