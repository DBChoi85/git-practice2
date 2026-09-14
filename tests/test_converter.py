import unittest
import xml.etree.ElementTree as ET

from mermaid_to_umlet import convert_text
from mermaid_to_umlet.layout import hierarchical_layout
from mermaid_to_umlet.parser import MermaidParseError, parse_mermaid


SOURCE = """classDiagram
class Animal {
  +String name
  +speak() void
}
class Dog
<<interface>> Animal
Animal "1" <|-- "*" Dog : extends
Dog : +fetch() bool
"""


class ConverterTests(unittest.TestCase):
    def test_parser(self):
        model = parse_mermaid(SOURCE)
        self.assertEqual(["+String name"], model.classes["Animal"].attributes)
        self.assertEqual(["+speak() void"], model.classes["Animal"].methods)
        self.assertEqual(["+fetch() bool"], model.classes["Dog"].methods)
        self.assertEqual("interface", model.classes["Animal"].stereotype)
        self.assertEqual("inheritance-reverse", model.relations[0].relation_type)
        self.assertEqual("1", model.relations[0].source_multiplicity)
        self.assertEqual("*", model.relations[0].target_multiplicity)

    def test_valid_uxf_xml(self):
        root = ET.fromstring(convert_text(SOURCE, columns=2))
        self.assertEqual("diagram", root.tag)
        self.assertEqual(3, len(root.findall("element")))

    def test_hierarchical_layout_places_parent_above_child(self):
        positioned = hierarchical_layout(parse_mermaid(SOURCE))
        self.assertLess(positioned.class_boxes["Animal"].y, positioned.class_boxes["Dog"].y)

    def test_reverse_inheritance_syntax(self):
        source = """classDiagram
        class Parent
        class Child
        Child --|> Parent
        """
        positioned = hierarchical_layout(parse_mermaid(source))
        self.assertLess(positioned.class_boxes["Parent"].y, positioned.class_boxes["Child"].y)

    def test_multiple_inheritance_uses_deepest_parent(self):
        source = """classDiagram
        class Root
        class Left
        class Right
        class Leaf
        Root <|-- Left
        Root <|-- Right
        Left <|-- Leaf
        Right <|-- Leaf
        """
        positioned = hierarchical_layout(parse_mermaid(source))
        boxes = positioned.class_boxes
        self.assertLess(boxes["Root"].y, boxes["Left"].y)
        self.assertEqual(boxes["Left"].y, boxes["Right"].y)
        self.assertLess(boxes["Left"].y, boxes["Leaf"].y)

    def test_cycle_falls_back_without_failure(self):
        source = """classDiagram
        class A
        class B
        A <|-- B
        B <|-- A
        """
        positioned = hierarchical_layout(parse_mermaid(source))
        self.assertEqual(positioned.class_boxes["A"].y, positioned.class_boxes["B"].y)

    def test_grid_layout_remains_available(self):
        root = ET.fromstring(convert_text(SOURCE, columns=2, layout="grid"))
        self.assertEqual("diagram", root.tag)

    def test_unknown_layout(self):
        with self.assertRaises(ValueError):
            convert_text(SOURCE, layout="radial")

    def test_missing_header(self):
        with self.assertRaises(MermaidParseError):
            parse_mermaid("class Foo")


if __name__ == "__main__":
    unittest.main()
