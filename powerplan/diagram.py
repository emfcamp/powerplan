from __future__ import annotations

from collections import OrderedDict, defaultdict
from datetime import date
from typing import TYPE_CHECKING

import pydotplus as pydot  # type: ignore

from . import ureg
from .cables import CableConfiguration, get_cable_ratings, select_cable_size
from .data import AMF, Distro, Generator, LogicalSource, PowerNode

if TYPE_CHECKING:
    from .plan import Plan

COLOUR_THREEPHASE = "firebrick3"
COLOUR_SINGLEPHASE = "blue4"
COLOUR_HEADER = "lightcyan1"


def _sanitise_name(name):
    return name.lower().replace(" ", "_").replace("-", "_")


def _render_port(current, phases, count=1):
    if phases == 1:
        colour = COLOUR_SINGLEPHASE
    elif phases == 3:
        colour = COLOUR_THREEPHASE

    txt = f'<font color="{colour}">'
    if count > 1:
        txt += f"{count} × "
    txt += f"{current}A {phases}ϕ"
    txt += "</font>"
    return txt


def calculate_max_length(
    V,
    Z_s,
    I_n: float,
    csa: float,
    methodology: str = "Eland",
    cable_config: CableConfiguration = CableConfiguration.TWO_CORE,
):
    """Calculate maximum length of a cable which will still satisfy the fault current requirement."""
    ratings = get_cable_ratings(csa, methodology, cable_config)
    if ratings is None:
        raise ValueError(
            f"No ratings found for CSA: {csa}mm², methodology {methodology}, configuration {cable_config}"
        )
    cable_r1 = (ratings["voltage_drop"] / 1000) * (ureg.ohm / ureg.meter)
    max_z_s = (V / (5.5 * I_n)).to(ureg.ohm)

    max_length = (max_z_s - Z_s) / (cable_r1 * 2)
    return max_length


def _unique_outputs(spec):
    types = defaultdict(lambda: 0)
    for out in spec["outputs"]:
        types[(out["current"], out["phases"])] += 1

    result = []

    for current, phases in sorted(
        types.keys(), key=lambda v: (v[0], v[1]), reverse=True
    ):
        result.append((current, phases, types[(current, phases)]))
    return result


def _node_additional(node: PowerNode) -> dict:
    "Additional detail for a node"
    additional = OrderedDict()

    final_circuit_lengths = None
    if isinstance(node, Distro | LogicalSource | AMF):
        z_s = node.z_s()
        if z_s:
            # Calculate Zs and prospective fault current at the input breaker of this distro.
            additional["Z<sub>s</sub>"] = f"{z_s:.4~H}"
            i_pf = node.i_pf()
            i_n = node.i_n()
            trip_ratio = (i_pf / i_n).magnitude
            trip_text = f"({trip_ratio:.1f}I<sub>n</sub>)"

            threshold = 5.5
            if trip_ratio < threshold:
                trip_text = f'<font color="red">{trip_text}</font>'
            additional["I<sub>pf (L-N)</sub>"] = f"{i_pf:.5~H} {trip_text}"

            # Select all single-phase outputs and calculate the longest cable length which will
            # provide an acceptable prospective fault current.
            #
            output_ratings = set(
                out["current"] * ureg.ampere
                for out in node.get_spec()["outputs"]
                if out["phases"] == 1
            )

            circuit_length_params: list[tuple[int, float]] = []
            for i_n in sorted(output_ratings, reverse=True):
                csa = select_cable_size(
                    i_n.magnitude, "4F3A", CableConfiguration.TWO_CORE
                )
                if csa is None:
                    continue
                circuit_length_params.append((i_n, float(csa)))

                if i_n == 16 * ureg.A:
                    # For 16A also include a worst-case 1.25 mm^2 CSA as these
                    # cables are sometimes seen.
                    circuit_length_params.append((i_n, 1.25))

            final_circuit_lengths = []
            for i_n, c_csa in circuit_length_params:
                # Calculate final circuit lengths using BS7671 table 4F3A (flexible, non-armoured)
                max_length = calculate_max_length(
                    node.voltage_ln, z_s, i_n, c_csa, methodology="4F3A"
                )
                final_circuit_lengths.append(
                    f"{max_length:.4~H} @ {i_n:~H} ({c_csa} mm<sup>2</sup>)"
                )

                # Adiabatic equation:
                # k = 115
                # print(i_n, (k**2 * csa**2) / (5.5 * i_n.magnitude) ** 2)

        v_drop = node.v_drop()
        if v_drop:
            drop_ratio = node.v_drop_ratio() * 100
            drop_text = f"({drop_ratio:.1f}%)"
            # Drop ratio limits from BS7671 Appendix 12
            if drop_ratio > 8:
                drop_text = f'<font color="red">{drop_text}</font>'
            elif drop_ratio > 6:
                drop_text = f'<font color="orange">{drop_text}</font>'
            additional["V<sub>drop</sub>"] = f"{v_drop:.3~H} {drop_text}"

    elif type(node) == Generator:
        additional["P<sub>o</sub>"] = f"{node.power:~H}"
        additional["U"] = f"{node.voltage:~H}"
        additional["Z<sub>e</sub>"] = "{:.4~H} ({:~H})".format(
            node.z_e(), node.get_spec().get("transient_reactance")
        )

    load = node.load()
    if load.magnitude > 0:
        additional["Load"] = "{:~H}".format(load.to(ureg("kW")))

    if final_circuit_lengths:
        additional["Max final<br/>circuit length"] = "<br/>".join(final_circuit_lengths)

    return additional


def _node_label(node: PowerNode) -> str:
    "Label format for a node. Using graphviz's HTML table support"
    spec = node.get_spec()

    label = '<<table border="0" cellborder="1" cellspacing="0" cellpadding="4" color="grey30">\n'
    label += """<tr><td bgcolor="{colour}"><font point-size="16"><b>{name}</b></font></td>
                    <td bgcolor="{colour}"><font point-size="16">{type}</font></td></tr>""".format(
        name=node.name, type=node.type or "No type assigned", colour=COLOUR_HEADER
    )
    if spec is None:
        label += '<tr><td port="input"></td></tr></table>>'
        return label

    num_inputs = len(spec["inputs"])
    unique_outputs = _unique_outputs(spec)
    label += (
        f'<tr><td port="input" rowspan="{max(len(unique_outputs), 1)}" align="left">'
    )
    if num_inputs > 0:
        label += _render_port(spec["inputs"][0]["current"], spec["inputs"][0]["phases"])
    label += "</td>"

    first = True
    for current, phases, count in unique_outputs:
        if not first:
            label += "<tr>"
        else:
            first = False

        label += f'<td port="{current}-{phases}" align="right">'
        label += _render_port(current, phases, count)
        label += "</td></tr>\n"

    if len(unique_outputs) == 0:
        label += "</tr>"

    for k, v in _node_additional(node).items():
        label += f'<tr><td align="right">{k}</td><td align="left">{v}</td></tr>'

    label += "</table>>"
    return label


def _title_label(name: str) -> str:
    label = '<<table border="0" cellspacing="0" cellborder="1" cellpadding="5">'
    label += f'<tr><td bgcolor="{COLOUR_HEADER}"><b>{name}</b></td></tr>'
    label += "<tr><td>Power Plan</td></tr>"
    label += f"<tr><td>{date.today().isoformat()}</td></tr>"
    label += "</table>>"
    return label


def _get_subgraph(plan: Plan):
    dot = pydot.Cluster(_sanitise_name(plan.name), label="Grid %s" % plan.name)
    for n in plan.nodes():
        if n.name is None:
            raise Exception(f"Nodes must all be named! {n} is missing a name")
        node = pydot.Node(n.name, label=_node_label(n))
        dot.add_node(node)

    for u, v, edge_data in plan.edges():
        edge = pydot.Edge(u.name, v.name)

        label = "{}A".format(edge_data["current"])

        if edge_data["phases"] == 3:
            colour = COLOUR_THREEPHASE
            label += " 3ϕ"
        else:
            colour = COLOUR_SINGLEPHASE

        if edge_data.get("csa"):
            label += " {}mm²".format(edge_data["csa"])

        if edge_data.get("cable_lengths"):
            label += "\n{}".format(
                " + ".join(str(length) + "m" for length in edge_data["cable_lengths"])
            )

            spare = sum(edge_data["cable_lengths"]) - edge_data["length"]
            label += f" ({spare}m spare)"

            if spare > edge_data["cable_lengths"][-1] * 0.8:
                edge.set_fontcolor("red")

        if not edge_data.get("logical"):
            edge.set_label(label)

        edge.set_tailport("{}-{}".format(edge_data["current"], edge_data["phases"]))
        edge.set_headport("input")
        edge.set_color(colour)
        dot.add_edge(edge)

    return dot


def to_dot(plan: Plan, split_subplans: bool = True):
    if not plan.spec:
        raise ValueError(
            "Diagrams can only be drawn of plans which have a spec assigned"
        )

    dot = pydot.Dot(plan.name or None, graph_type="digraph", strict=True)
    dot.set_node_defaults(shape="none", fontsize=14, margin=0, fontname="Arial")
    dot.set_edge_defaults(fontsize=13, fontname="Arial")
    # dot.set_page('11.7,8.3!')
    # dot.set_margin(0.5)
    # dot.set_ratio('fill')
    dot.set_rankdir("LR")
    dot.set_fontname("Arial")
    dot.set_nodesep(0.3)

    if split_subplans:
        grids = plan.grids()
    else:
        grids = [plan]

    for grid in grids:
        sg = _get_subgraph(grid)
        sg.set_color("gray80")
        sg.set_style("dashed")
        sg.set_labeljust("l")
        dot.add_subgraph(sg)

    title = pydot.Node(
        "title", shape="none", label=_title_label(plan.name or "[UNNAMED]")
    )
    title.set_pos("0,0!")
    title.set_fontsize(18)
    dot.add_node(title)

    return dot
