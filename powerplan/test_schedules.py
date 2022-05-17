from __future__ import annotations
from re import L
from typing import TYPE_CHECKING
from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from .plan import Plan

env = Environment(
    loader=PackageLoader("powerplan", "templates"), autoescape=select_autoescape(["html", "xml"])
)

# FIXME: This probably shouldn't live here...
ADJUSTABLE = ["Adjustable", "adjustable", "100-1000mA"]


def generate_schedule(plan: Plan):
    tests = {}

    for grid in plan.grids():
        tests[grid.name] = {}

        longest = None

        for a, b, data in grid.edges():
            three_phase_output = False
            if not longest:
                longest = b

            for c, c_data in b.outputs():
                # Test each adjustable RCD
                if c_data["rcd"] in ADJUSTABLE:
                    print(c.name, "adjustable")
                    tests[grid.name][c.name] = {
                        "source": b,
                        "node": c,
                        "data": c_data,
                    }

                # Check if there are any used 3ph outputs
                if c_data["phases"] == 3:
                    three_phase_output = True

            # Test the end of each three phase run
            if data["phases"] == 3 and not three_phase_output:
                print(b.name, "end of run")
                tests[grid.name][b.name] = {
                    "source": a,
                    "node": b,
                    "data": data,
                }

            # Test a circuit from the longest submain of each grid
            # FIXME: can return inconsistent results for matching distances based on .outputs() sort order
            if b.cable_length_from_source() > longest.cable_length_from_source():
                longest = b

            # Test control position supply from each powercube
            if b.get_spec()["ref"] == "Powercube":
                # FIXME: Better selection of output and add RCD to powercube spec
                name = b.name + "-pc"
                output = b.get_spec()["outputs"][0]
                output["rcd"] = "30mA"
                print(name, "powercube")
                tests[grid.name][name] = {
                    "description": "Control position power from " + b.name,
                    "source": b,
                    "data": output,
                    "final": True,
                }

        # Test the distro further from the source
        if longest:
            print(b.name, "longest")
            tests[grid.name][b.name] = {
                "source": a,
                "node": b,
                "data": data,
            }

        # Sort alphabetically by key
        tests[grid.name] = sorted(tests[grid.name].items())

    return tests


def generate_schedule_html(plan: Plan):
    tests = generate_schedule(plan)
    template = env.get_template("test_schedules.html")
    return template.render(tests=tests, plan=plan, adjustable=ADJUSTABLE)
