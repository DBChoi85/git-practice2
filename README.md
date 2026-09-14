# Mermaid to UMLet

A dependency-free Python MVP that converts Mermaid `classDiagram` source into an editable UMLet `.uxf` file.

## Supported syntax

- Classes, aliases, attributes, and methods
- Stereotypes such as `<<interface>>` and `<<abstract>>`
- Inheritance and implementation
- Directed and undirected associations
- Aggregation, composition, and dependency
- Multiplicities and relationship labels
- Notes attached to classes
- Hierarchical layout based on inheritance and implementation relationships
- Multiple roots, multiple inheritance, disconnected classes, and cycle fallback
- Deterministic grid layout as an alternative

This is intentionally a supported subset of Mermaid rather than a complete Mermaid parser.

## Quick start

Run directly from the project directory:

```bash
PYTHONPATH=src python -m mermaid_to_umlet.cli examples/school.mmd -o examples/school.uxf
```

Or install it:

```bash
python -m pip install .
mermaid-to-umlet examples/school.mmd -o examples/school.uxf
```

Choose the number of columns:

```bash
mermaid-to-umlet examples/school.mmd -o examples/school.uxf --layout grid --columns 2
```

Hierarchical layout is the default. Parent classes and interfaces are placed
above descendants:

```bash
mermaid-to-umlet examples/inheritance.mmd -o examples/inheritance.uxf --layout hierarchical
```

Open the generated `school.uxf` in UMLet. The initial positions are generated automatically and remain editable.

## Python API

```python
from mermaid_to_umlet import convert_text

source = """classDiagram
class User {
  +String name
  +login() bool
}
"""

uxf_xml = convert_text(source, layout="hierarchical")
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Current limitations

- Only Mermaid `classDiagram` is supported.
- Hierarchical ordering is graph-aware, but routing does not yet avoid every line crossing.
- Relationship label placement follows UMLet defaults.
- Mermaid generics and quoted identifiers are only partially supported.
- Notes are rendered, but no connector is drawn from a note to its class.
