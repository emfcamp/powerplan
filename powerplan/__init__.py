import pint

ureg = pint.UnitRegistry(
    preprocessors=[
        lambda s: s.replace("%", " percent "),
    ]
)
ureg.define("percent = 0.01 = %")

from .plan import Plan  # noqa: E402
from .data import Generator, Distro, Load, AMF  # noqa: E402
from .spec import EquipmentSpec  # noqa: E402

__all__ = ["Plan", "EquipmentSpec", "Generator", "Distro", "AMF", "Load", "ureg"]
