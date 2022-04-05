from __future__ import annotations
from re import L
from typing import TYPE_CHECKING
from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from .plan import Plan

env = Environment(
    loader=PackageLoader("powerplan", "templates"), autoescape=select_autoescape(["html", "xml"])
)


def generate_schedule(plan: Plan):
    tests = []
    for node in plan.nodes():
        # Don't include generator nodes in test sheet
        if node.get_spec()["type"] == "generator":
            continue

        # Test schedule entry for each RCD type per distro
        output_types = {}
        for output in node.get_spec()["outputs"]:
            device_type = str(output["phases"]) + getattr(output, 'rcd', '')
            output_types[device_type] = output

        for test in output_types:
            output = output_types[test]
            tests.append({
                "type": type(node).__name__,
                "name": node.name,
                "phases": output["phases"],
                "current": output["current"],
                "rcd": output.get("rcd", ""),
            })

    return tests


def generate_schedule_html(plan: Plan):
    tests = generate_schedule(plan)
    template = env.get_template("test_schedules.html")
    return template.render(tests=tests, plan=plan)
