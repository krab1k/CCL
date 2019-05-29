"""Generate a graph representation of CCL's abstract syntax tree in dot format"""

import itertools
import html
from typing import List, Dict, Union
from enum import Enum

from ccl import ast, symboltable

__all__ = ['Graphviz']


class GraphNode:
    def __init__(self, idx: int, node_type: str) -> None:
        self.idx: int = idx
        self.node_type: str = node_type
        self.properties: List[str] = []

    def __str__(self) -> str:
        property_string = '<br/>'.join(prop for prop in self.properties if not prop.startswith('_'))
        return f'node{self.idx} [label = < <b>{self.node_type}</b><br/> {property_string} >]'


class SymbolTableNode:
    def __init__(self, idx: int, symbols: Dict[str, symboltable.Symbol]) -> None:
        self.idx: int = idx
        self.symbols: List[str] = []
        for name, symbol in symbols.items():
            props = ', '.join(f'{k} = {symbol.__dict__[k]}' for k in symbol.__dict__ if k not in ['name', 'def_node'])
            self.symbols.append(html.escape(f'{name}: {symbol.__class__.__name__} ({props})'))

    def __str__(self) -> str:
        symbols_string = '<br/>'.join(self.symbols)
        return f'node{self.idx} [label = < <b> SymbolTable </b><br/> {symbols_string} >]'


class Graphviz(ast.ASTVisitor):
    def __init__(self, table: symboltable.SymbolTable, **kwargs) -> None:
        super().__init__()
        self.nodes: List[Union[GraphNode, SymbolTableNode]] = []
        self.edges: List[str] = []
        gn = GraphNode(0, 'Method')
        self.nodes.append(gn)
        self.current_node: GraphNode = gn
        self.symboltable: symboltable.SymbolTable = table

    def _visit(self, field: str, node: ast.ASTNode) -> None:
        gn = GraphNode(len(self.nodes) + 1, node.__class__.__name__)
        self.nodes.append(gn)
        self.edges.append(f'node{self.current_node.idx} -> node{gn.idx} [label = "{field}"]')
        old = self.current_node
        self.current_node = gn
        self.visit(node)
        self.current_node = old

    def print_symbol_table(self, table: symboltable.SymbolTable):
        gn = SymbolTableNode(len(self.nodes) + 1, table.symbols)
        self.nodes.append(gn)
        self.edges.append(f'node{self.current_node.idx} -> node{gn.idx}')

    def generic_visit(self, node: ast.ASTNode) -> None:
        for field, value in node:
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, ast.ASTNode):
                        self._visit(f'{field}:{idx}', item)
            elif isinstance(value, ast.ASTNode):
                self._visit(field, value)
            else:
                if isinstance(value, Enum):
                    self.current_node.properties.append(html.escape(f'{field} = {value.value}'))
                elif isinstance(value, symboltable.SymbolTable):
                    self.print_symbol_table(value)
                else:
                    self.current_node.properties.append(f'{field} = {value}')

    def visit_Method(self, node: ast.Method) -> str:
        self.generic_visit(node)

        data = ''
        for item in itertools.chain(self.nodes, self.edges):
            data += f'{item}\n'

        return f'digraph G {{\nnode [shape=rectangle]\n{data}}}'
