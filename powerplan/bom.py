from __future__ import annotations
from typing import TYPE_CHECKING
from collections import defaultdict
from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from .plan import Plan

env = Environment(
    loader=PackageLoader("powerplan", "templates"), autoescape=select_autoescape(["html", "xml"])
)


def generate_bom(plan: Plan):
    node_types = defaultdict(list)
    for node in plan.nodes():
        node_types[(type(node).__name__, node.type)].append(node.name)

    edge_types = defaultdict(list)

    for u, v, data in plan.edges():
        if data.get("logical"):
            continue
        for length in data["cable_lengths"]:
            edge_types[(data["current"], data["phases"], length)].append("%s -> %s" % (u.name, v.name))

    return node_types, edge_types


def generate_bom_html(plan: Plan):
    nodes, edges = generate_bom(plan)
    template = env.get_template("bom.html")
    return template.render(nodes=nodes, edges=edges, plan=plan)
