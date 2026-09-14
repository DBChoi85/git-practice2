from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UMLClass:
    identifier: str
    name: str
    stereotype: str | None = None
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class UMLRelation:
    source: str
    target: str
    relation_type: str
    source_multiplicity: str | None = None
    target_multiplicity: str | None = None
    label: str | None = None


@dataclass
class UMLNote:
    target: str | None
    text: str


@dataclass
class UMLModel:
    classes: dict[str, UMLClass] = field(default_factory=dict)
    relations: list[UMLRelation] = field(default_factory=list)
    notes: list[UMLNote] = field(default_factory=list)

    def ensure_class(self, identifier: str, display_name: str | None = None) -> UMLClass:
        if identifier not in self.classes:
            self.classes[identifier] = UMLClass(identifier, display_name or identifier)
        elif display_name:
            self.classes[identifier].name = display_name
        return self.classes[identifier]


@dataclass
class Box:
    x: int
    y: int
    width: int
    height: int


@dataclass
class PositionedModel:
    model: UMLModel
    class_boxes: dict[str, Box]
    note_boxes: list[Box]

