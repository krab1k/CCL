import itertools
import html
from typing import List
from enum import Enum

from ccl.ast import *


__all__ = ['Graphviz']


class GraphNode:
    def __init__(self, idx: int, node_type: str) -> None:
        self.idx: int = idx
        self.node_type: str = node_type
        self.properties: List[str] = []

    def __str__(self) -> str:
        property_string = '<br/>'.join(prop for prop in self.properties)
        return f'node{self.idx} [label = < <b>{self.node_type}</b><br/> {property_string} >]'


class Graphviz(ASTVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: List[GraphNode] = []
        self.edges: List[str] = []
        gn = GraphNode(0, 'Method')
        self.nodes.append(gn)
        self.current_node: GraphNode = gn

    def _visit(self, field: str, node: ASTNode) -> None:
        gn = GraphNode(len(self.nodes) + 1, node.__class__.__name__)
        self.nodes.append(gn)
        self.edges.append(f'node{self.current_node.idx} -> node{gn.idx} [label = "{field}"]')
        old = self.current_node
        self.current_node = gn
        self.visit(node)
        self.current_node = old

    def generic_visit(self, node: ASTNode) -> None:
        for field, value in node:
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, ASTNode):
                        self._visit(f'{field}:{idx}', item)
            elif isinstance(value, ASTNode):
                self._visit(field, value)
            else:
                if isinstance(value, Enum):
                    self.current_node.properties.append(html.escape(f'{field} = {value.value}'))
                else:
                    self.current_node.properties.append(f'{field} = {value}')

    def visit_Method(self, node: Method) -> str:
        self.generic_visit(node)

        data = ''
        for item in itertools.chain(self.nodes, self.edges):
            data += f'{item}\n'

        return f'digraph G {{\nnode [shape=rectangle]\n{data}}}'
