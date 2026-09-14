from __future__ import annotations

from .layout import grid_layout, hierarchical_layout
from .parser import parse_mermaid
from .umlet_writer import generate_uxf


def convert_text(source: str, columns: int = 3, layout: str = "hierarchical") -> str:
    model = parse_mermaid(source)
    if layout == "hierarchical":
        positioned = hierarchical_layout(model)
    elif layout == "grid":
        positioned = grid_layout(model, columns=columns)
    else:
        raise ValueError("layout must be 'hierarchical' or 'grid'")
    return generate_uxf(positioned)
