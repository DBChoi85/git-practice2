from __future__ import annotations

import math
from collections import defaultdict, deque

from .model import Box, PositionedModel, UMLModel


def _class_dimensions(model: UMLModel) -> dict[str, tuple[int, int]]:
    dimensions: dict[str, tuple[int, int]] = {}
    for uml_class in model.classes.values():
        longest = max(
            [len(uml_class.name), *(len(x) for x in uml_class.attributes), *(len(x) for x in uml_class.methods)],
            default=12,
        )
        width = max(220, min(420, 28 + longest * 8))
        rows = 1 + bool(uml_class.stereotype) + len(uml_class.attributes) + len(uml_class.methods)
        height = max(100, 52 + rows * 20)
        dimensions[uml_class.identifier] = (width, height)
    return dimensions


def _note_boxes(model: UMLModel, boxes: dict[str, Box], fallback_y: int, margin: int) -> list[Box]:
    result: list[Box] = []
    for index, note in enumerate(model.notes):
        target = boxes.get(note.target or "")
        height = max(80, 40 + 18 * note.text.count("\n"))
        if target:
            result.append(Box(target.x + target.width + 30, target.y, 220, height))
        else:
            result.append(Box(margin, fallback_y + index * 100, 220, height))
    return result


def grid_layout(
    model: UMLModel,
    columns: int = 3,
    margin: int = 40,
    horizontal_gap: int = 100,
    vertical_gap: int = 100,
) -> PositionedModel:
    if columns < 1:
        raise ValueError("columns must be at least 1")

    boxes: dict[str, Box] = {}
    class_list = list(model.classes.values())
    max_width = 220
    row_heights: dict[int, int] = {}

    dimensions_by_id = _class_dimensions(model)
    dimensions = [dimensions_by_id[item.identifier] for item in class_list]
    max_width = max([220, *(width for width, _ in dimensions)])

    for index, (_, height) in enumerate(dimensions):
        row = index // columns
        row_heights[row] = max(row_heights.get(row, 0), height)

    row_y: dict[int, int] = {}
    cursor_y = margin
    for row in range(math.ceil(len(class_list) / columns)):
        row_y[row] = cursor_y
        cursor_y += row_heights[row] + vertical_gap

    for index, uml_class in enumerate(class_list):
        row, column = divmod(index, columns)
        width, height = dimensions[index]
        boxes[uml_class.identifier] = Box(
            x=margin + column * (max_width + horizontal_gap),
            y=row_y[row],
            width=width,
            height=height,
        )

    return PositionedModel(model=model, class_boxes=boxes, note_boxes=_note_boxes(model, boxes, cursor_y, margin))


def _inheritance_edges(model: UMLModel) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return parent->children and child->parents maps for inheritance-like relations."""
    children: dict[str, set[str]] = defaultdict(set)
    parents: dict[str, set[str]] = defaultdict(set)
    for relation in model.relations:
        if relation.relation_type in {"inheritance-reverse", "implementation-reverse"}:
            parent, child = relation.source, relation.target
        elif relation.relation_type in {"inheritance", "implementation"}:
            parent, child = relation.target, relation.source
        else:
            continue
        children[parent].add(child)
        parents[child].add(parent)
    return children, parents


def hierarchical_layout(
    model: UMLModel,
    margin: int = 40,
    horizontal_gap: int = 100,
    vertical_gap: int = 120,
) -> PositionedModel:
    """Place inheritance roots at the top and descendants on lower levels.

    The longest parent path determines a class's level. Multiple inheritance is
    supported. Classes in an invalid inheritance cycle are kept together on a
    final level so conversion remains deterministic and usable.
    """
    if not model.classes:
        return PositionedModel(model=model, class_boxes={}, note_boxes=[])

    class_ids = list(model.classes)
    source_order = {class_id: index for index, class_id in enumerate(class_ids)}
    children, parents = _inheritance_edges(model)
    indegree = {class_id: len(parents[class_id]) for class_id in class_ids}
    levels = {class_id: 0 for class_id in class_ids}
    queue = deque(class_id for class_id in class_ids if indegree[class_id] == 0)
    processed: list[str] = []

    while queue:
        parent = queue.popleft()
        processed.append(parent)
        for child in sorted(children[parent], key=source_order.get):
            levels[child] = max(levels[child], levels[parent] + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    # A valid UML inheritance graph is acyclic. Keep malformed cycle members on
    # one final row instead of rejecting the entire conversion.
    cyclic = [class_id for class_id in class_ids if class_id not in set(processed)]
    if cyclic:
        cycle_level = max((levels[item] for item in processed), default=-1) + 1
        for class_id in cyclic:
            levels[class_id] = cycle_level

    grouped: dict[int, list[str]] = defaultdict(list)
    for class_id in class_ids:
        grouped[levels[class_id]].append(class_id)

    # Parent-centred ordering reduces crossings while retaining stable source order.
    previous_positions: dict[str, int] = {}
    for level in sorted(grouped):
        def order_key(class_id: str) -> tuple[float, int]:
            known = [previous_positions[p] for p in parents[class_id] if p in previous_positions]
            return ((sum(known) / len(known)) if known else float(source_order[class_id]), source_order[class_id])

        grouped[level].sort(key=order_key)
        previous_positions.update({class_id: index for index, class_id in enumerate(grouped[level])})

    dimensions = _class_dimensions(model)
    row_widths = {
        level: sum(dimensions[item][0] for item in items) + horizontal_gap * max(0, len(items) - 1)
        for level, items in grouped.items()
    }
    canvas_width = max(row_widths.values())
    boxes: dict[str, Box] = {}
    cursor_y = margin

    for level in sorted(grouped):
        items = grouped[level]
        cursor_x = margin + (canvas_width - row_widths[level]) // 2
        row_height = max(dimensions[item][1] for item in items)
        for class_id in items:
            width, height = dimensions[class_id]
            boxes[class_id] = Box(cursor_x, cursor_y, width, height)
            cursor_x += width + horizontal_gap
        cursor_y += row_height + vertical_gap

    return PositionedModel(model=model, class_boxes=boxes, note_boxes=_note_boxes(model, boxes, cursor_y, margin))
