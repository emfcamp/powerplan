from datetime import date
import pydotplus as pydot
from collections import defaultdict, OrderedDict

from . import ureg
from .data import Distro, Generator

COLOUR_THREEPHASE = 'firebrick3'
COLOUR_SINGLEPHASE = 'blue4'
COLOUR_HEADER = 'lightcyan1'


def _render_port(current, phases, count=1):
    if phases == 1:
        colour = COLOUR_SINGLEPHASE
    elif phases == 3:
        colour = COLOUR_THREEPHASE

    txt = '<font color="{}">'.format(colour)
    if count > 1:
        txt += '{} × '.format(count)
    txt += "{}A {}ϕ".format(current, phases)
    txt += "</font>"
    return txt


def _unique_outputs(spec):
    types = defaultdict(lambda: 0)
    for out in spec['outputs']:
        types[(out['current'], out['phases'])] += 1

    result = []

    for current, phases in sorted(types.keys(), key=lambda v: (v[0], v[1]), reverse=True):
        result.append((current, phases, types[(current, phases)]))
    return result


def _node_additional(node):
    " Additional detail for a node "
    additional = OrderedDict()

    if type(node) == Distro:
        z_s = node.z_s()
        if z_s:
            additional['Z<sub>s</sub>'] = '{:.4~H}'.format(z_s)
            i_pf = node.i_pf()
            i_n = list(node.inputs())[0][1]['current'] * ureg('A')
            trip_ratio = (i_pf / i_n).magnitude
            trip_text = "({:.1f}I<sub>n</sub>)".format(trip_ratio)
            if trip_ratio < 5:
                trip_text = '<font color="red">{}</font>'.format(trip_text)
            additional['I<sub>pf (L-N)</sub>'] = '{:.5~H} {}'.format(
                i_pf, trip_text)

        v_drop = node.v_drop()
        if v_drop:
            drop_ratio = node.v_drop_ratio() * 100
            drop_text = '({:.1f}%)'.format(drop_ratio)
            # Drop ratio limits from BS7671 Appendix 12
            if drop_ratio > 8:
                drop_text = '<font color="red">{}</font>'.format(drop_text)
            elif drop_ratio > 6:
                drop_text = '<font color="orange">{}</font>'.format(drop_text)
            additional['V<sub>drop</sub>'] = '{:.3~H} {}'.format(v_drop, drop_text)

    elif type(node) == Generator:
        additional['P<sub>o</sub>'] = '{:~H}'.format(node.power)
        additional['U'] = '{:~H}'.format(node.voltage)
        additional['Z<sub>e</sub>'] = '{:.4~H} ({}%)'.format(
            node.z_e(), node.get_spec().get('transient_reactance'))

    load = node.load()
    if load.magnitude > 0:
        additional['Load'] = '{:~H}'.format(load.to(ureg('kW')))

    return additional


def _node_label(node):
    " Label format for a node. Using graphviz's HTML table support "
    spec = node.get_spec()

    label = '<<table border="0" cellborder="1" cellspacing="0" cellpadding="4" color="grey30">\n'
    label += '''<tr><td bgcolor="{colour}"><font point-size="16"><b>{name}</b></font></td>
                    <td bgcolor="{colour}"><font point-size="16">{type}</font></td></tr>'''.format(
        name=node.name, type=node.type or 'No type assigned', colour=COLOUR_HEADER)
    if spec is None:
        label += '<tr><td port="input"></td></tr></table>>'
        return label

    num_inputs = len(spec['inputs'])
    unique_outputs = _unique_outputs(spec)
    label += '<tr><td port="input" rowspan="{}" align="left">'.format(max(len(unique_outputs), 1))
    if num_inputs > 0:
        label += _render_port(spec['inputs'][0]['current'], spec['inputs'][0]['phases'])
    label += '</td>'

    first = True
    for current, phases, count in unique_outputs:
        if not first:
            label += '<tr>'
        else:
            first = False

        label += '<td port="{}-{}" align="right">'.format(current, phases)
        label += _render_port(current, phases, count)
        label += '</td></tr>\n'

    if len(unique_outputs) == 0:
        label += '</tr>'

    for k, v in _node_additional(node).items():
        label += '<tr><td align="right">{}</td><td align="left">{}</td></tr>'.format(k, v)

    label += '</table>>'
    return label


def _title_label(name):
    label = '<<table border="0" cellspacing="0" cellborder="1" cellpadding="5">'
    label += '<tr><td bgcolor="{}"><b>{}</b></td></tr>'.format(COLOUR_HEADER, name)
    label += '<tr><td>Power Plan</td></tr>'
    label += '<tr><td>{}</td></tr>'.format(date.today().isoformat())
    label += '</table>>'
    return label


def _get_subgraph(plan):
    dot = pydot.Cluster(plan.name, label="Grid %s" % plan.name)
    for n, nodedata in plan.nodes(data=True):
        if n.name is None:
            raise Exception("Nodes must all be named! {} is missing a name".format(n))
        node = pydot.Node(n.name, label=_node_label(n))
        dot.add_node(node)

    for u, v, edgedata in plan.edges(data=True):
        edge = pydot.Edge(u.name, v.name)

        label = '{}A'.format(edgedata['current'])

        if edgedata['phases'] == 3:
            colour = COLOUR_THREEPHASE
            label += ' 3ϕ'
        else:
            colour = COLOUR_SINGLEPHASE

        if edgedata.get('csa'):
            label += ' {}mm²'.format(edgedata['csa'])

        if edgedata.get('cable_lengths'):
            label += '\n{} ({}m spare)'.format(
                " + ".join(str(l) + 'm' for l in edgedata['cable_lengths']),
                sum(edgedata['cable_lengths']) - edgedata['length'])

        edge.set_tailport('{}-{}'.format(edgedata['current'], edgedata['phases']))
        edge.set_headport('input')
        edge.set_label(label)
        edge.set_color(colour)
        dot.add_edge(edge)

    return dot


def to_dot(plan):
    if not plan.spec:
        raise ValueError("Diagrams can only be drawn of plans which have a spec assigned")

    dot = pydot.Dot(plan.name or None, graph_type='digraph', strict=True)
    dot.set_node_defaults(shape='none', fontsize=14, margin=0, fontname='Arial')
    dot.set_edge_defaults(fontsize=13, fontname='Arial')
    # dot.set_page('11.7,8.3!')
    # dot.set_margin(0.5)
    # dot.set_ratio('fill')
    dot.set_rankdir('LR')
    dot.set_fontname('Arial')
    dot.set_nodesep(0.3)
    # dot.set_splines('line')

    for grid in plan.grids():
        sg = _get_subgraph(grid)
        sg.set_color('gray80')
        sg.set_style('dashed')
        sg.set_labeljust('l')
        dot.add_subgraph(sg)

    title = pydot.Node('title', shape='none', label=_title_label(plan.name))
    title.set_pos('0,0!')
    title.set_fontsize(18)
    dot.add_node(title)

    return dot
