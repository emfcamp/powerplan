import json
import click
from ..plan import from_json
from ..spec import EquipmentSpec


def load_json(fname):
    with open(fname, 'r') as f:
        return json.load(f)


@click.command()
@click.argument('nodes_file')
@click.argument('links_file')
@click.argument('spec_dir')
def run(nodes_file, links_file, spec_dir):
    nodes = load_json(nodes_file)
    links = load_json(links_file)
    spec = EquipmentSpec(spec_dir)
    plan = from_json(nodes, links, spec)
    print('test')
