from __future__ import annotations

import re

from .model import UMLModel, UMLRelation, UMLNote


RELATIONS = {
    "<|--": "inheritance-reverse",
    "--|>": "inheritance",
    "<|..": "implementation-reverse",
    "..|>": "implementation",
    "*--": "composition-reverse",
    "--*": "composition",
    "o--": "aggregation-reverse",
    "--o": "aggregation",
    "<--": "association-reverse",
    "-->": "association",
    "<..": "dependency-reverse",
    "..>": "dependency",
    "--": "link",
    "..": "dashed-link",
}

REL_TOKEN = r"(?:<\|--|--\|>|<\|\.\.|\.\.\|>|\*--|--\*|o--|--o|<--|-->|<\.\.|\.\.>|--|\.\.)"
REL_RE = re.compile(
    rf'^\s*([\w.:-]+)\s*(?:"([^"]+)")?\s*({REL_TOKEN})\s*'
    rf'(?:"([^"]+)")?\s*([\w.:-]+)\s*(?::\s*(.+))?\s*$'
)
CLASS_START_RE = re.compile(
    r'^\s*class\s+([\w.:-]+)(?:\["([^"]+)"\])?(?:\s+as\s+([\w.:-]+))?\s*(\{)?\s*$'
)
MEMBER_RE = re.compile(r"^\s*([\w.:-]+)\s*:\s*(.+)$")
ANNOTATION_RE = re.compile(r"^\s*<<\s*([^>]+?)\s*>>\s+([\w.:-]+)\s*$")
NOTE_RE = re.compile(r'^\s*note\s+for\s+([\w.:-]+)\s+"(.*)"\s*$')


class MermaidParseError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    return line.split("%%", 1)[0].strip()


def _add_member(model: UMLModel, class_id: str, member: str) -> None:
    member = member.strip()
    if not member:
        return
    uml_class = model.ensure_class(class_id)
    if "(" in member and ")" in member:
        uml_class.methods.append(member)
    else:
        uml_class.attributes.append(member)


def parse_mermaid(source: str) -> UMLModel:
    """Parse the supported subset of Mermaid classDiagram syntax."""
    model = UMLModel()
    current_class: str | None = None
    saw_header = False

    for line_no, raw_line in enumerate(source.splitlines(), 1):
        line = _strip_comment(raw_line)
        if not line:
            continue
        if line == "classDiagram" or line.startswith("classDiagram-"):
            saw_header = True
            continue
        if line.startswith("direction "):
            continue
        if current_class:
            if line == "}":
                current_class = None
            else:
                _add_member(model, current_class, line)
            continue

        match = CLASS_START_RE.match(line)
        if match:
            raw_id, bracket_name, alias, has_brace = match.groups()
            identifier = alias or raw_id
            display_name = bracket_name or raw_id
            model.ensure_class(identifier, display_name)
            if has_brace:
                current_class = identifier
            continue

        match = ANNOTATION_RE.match(line)
        if match:
            stereotype, class_id = match.groups()
            model.ensure_class(class_id).stereotype = stereotype.strip()
            continue

        match = NOTE_RE.match(line)
        if match:
            target, text = match.groups()
            model.ensure_class(target)
            model.notes.append(UMLNote(target=target, text=text.replace("\\n", "\n")))
            continue

        match = REL_RE.match(line)
        if match:
            source_id, source_mult, token, target_mult, target_id, label = match.groups()
            model.ensure_class(source_id)
            model.ensure_class(target_id)
            model.relations.append(
                UMLRelation(
                    source=source_id,
                    target=target_id,
                    relation_type=RELATIONS[token],
                    source_multiplicity=source_mult,
                    target_multiplicity=target_mult,
                    label=label.strip() if label else None,
                )
            )
            continue

        match = MEMBER_RE.match(line)
        if match:
            class_id, member = match.groups()
            model.ensure_class(class_id)
            _add_member(model, class_id, member)
            continue

        raise MermaidParseError(f"Unsupported syntax at line {line_no}: {raw_line.strip()}")

    if not saw_header:
        raise MermaidParseError("Input must contain a classDiagram header")
    if current_class:
        raise MermaidParseError(f"Class block for {current_class!r} is not closed")
    return model

