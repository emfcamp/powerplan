from __future__ import annotations

import csv
from collections import defaultdict
from typing import TYPE_CHECKING, TextIO
from .data import Generator, Distro

from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from .plan import Plan

env = Environment(
    loader=PackageLoader("powerplan", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def generate_bom(plan: Plan):
    if plan.spec is None:
        raise ValueError("Plan has no spec")

    node_types = defaultdict(list)
    for node in plan.nodes():
        node_types[(type(node), node.type)].append(node.name)

    node_data: list[dict] = []

    for (node_type, node_model), nodes in node_types.items():
        if node_type is Generator:
            spec = plan.spec.generator[node_model]
        elif node_type is Distro:
            spec = plan.spec.distro[node_model]
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

        node_data.append(
            {
                "type": node_type.__name__,
                "model": node_model,
                "uses": sorted(nodes),
                "supplier": spec["supplier"],
            }
        )

    edge_types = defaultdict(list)

    for u, v, data in plan.edges():
        if data.get("logical"):
            continue
        for length in data.get("cable_lengths", []):
            edge_types[(data["current"], data["phases"], length)].append(
                f"{u.name} -> {v.name}"
            )

    return node_data, edge_types


def generate_bom_html(plan: Plan):
    nodes, edges = generate_bom(plan)
    template = env.get_template("bom.html")
    return template.render(nodes=nodes, edges=edges, plan=plan)


def generate_bom_csvs(plan: Plan, distros_file: TextIO, cables_file: TextIO):
    nodes, edges = generate_bom(plan)
    distros_writer = csv.writer(distros_file)
    distros_writer.writerow(["supplier", "type", "part", "count"])
    for node in nodes:
        distros_writer.writerow(
            [node["supplier"], node["type"], node["model"], len(node["uses"])]
        )

    cables_writer = csv.writer(cables_file)
    cables_writer.writerow(["I", "phases", "length", "count"])
    for edge_type, used in edges.items():
        cables_writer.writerow([edge_type[0], edge_type[1], edge_type[2], len(used)])
