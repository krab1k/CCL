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
        property_string = '<br/>'.join(prop for prop in self.properties if not prop.startswith('_') or prop == '_result_type')
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
        return f'st_node{self.idx} [shape = note color=grey label = < <b> SymbolTable </b><br/> {symbols_string} >]'


class Graphviz(ast.ASTVisitor):
    def __init__(self, table: symboltable.SymbolTable, **kwargs) -> None:
        super().__init__()
        self.nodes: List[GraphNode] = []
        self.symbol_table_nodes: List[SymbolTableNode] = []
        self.edges: List[str] = []
        gn = GraphNode(0, 'Method')
        self.nodes.append(gn)
        self.current_node: GraphNode = gn
        self.current_table_node: SymbolTableNode = SymbolTableNode(len(self.symbol_table_nodes) + 1, table.parent.symbols)
        self.symbol_table_nodes.append(self.current_table_node)

        self.annotate_results: bool = False
        try:
            if kwargs['annotate_results']:
                self.annotate_results = True
        except KeyError:
            pass

    def _visit(self, field: str, node: ast.ASTNode) -> GraphNode:
        gn = GraphNode(len(self.nodes) + 1, node.__class__.__name__)
        self.nodes.append(gn)
        self.edges.append(f'node{self.current_node.idx} -> node{gn.idx} [label = "{field}"]')
        old = self.current_node
        self.current_node = gn

        if isinstance(node, (ast.For, ast.ForEach)):
            st = SymbolTableNode(len(self.symbol_table_nodes) + 1, node.symbol_table.symbols)
            self.symbol_table_nodes.append(st)
            self.edges.append(f'node{self.current_node.idx} -> st_node{st.idx} [color=grey dir=none]')
            self.edges.append(f'st_node{self.current_table_node.idx} -> st_node{st.idx} [color=grey dir=back]')
            old_table = self.current_table_node
            self.current_table_node = st
            self.visit(node)
            self.current_table_node = old_table
        else:
            self.visit(node)

        if self.annotate_results:
            if isinstance(node, ast.Expression):
                self.current_node.properties.append(f'<font color="red"> result_type ='
                                                    f'{html.escape(str(node.result_type))}</font>')
        self.current_node = old

        return gn

    def generic_visit(self, node: ast.ASTNode) -> None:
        for field, value in node:
            if isinstance(value, list):
                same_level = []
                for idx, item in enumerate(value):
                    if isinstance(item, ast.ASTNode):
                        gn = self._visit(f'{field}:{idx}', item)
                        same_level.append(f'node{gn.idx}')
                if len(same_level) > 1:
                    self.edges.append(' -> '.join(same_level) + '[style = invis]')
                    self.edges.append('{rank=same; ' + '; '.join(same_level) + '}')
            elif isinstance(value, ast.ASTNode):
                self._visit(field, value)
            else:
                if isinstance(value, Enum):
                    self.current_node.properties.append(html.escape(f'{field} = {value.value}'))
                elif field == 'symbol_table':
                    pass
                else:
                    self.current_node.properties.append(f'{field} = {value}')

    def visit_Method(self, node: ast.Method) -> str:
        st = SymbolTableNode(len(self.symbol_table_nodes) + 1, node.symbol_table.symbols)
        self.symbol_table_nodes.append(st)
        self.edges.append(f'node{self.current_node.idx} -> st_node{st.idx} [color=grey dir=none]')
        self.edges.append(f'st_node{self.current_table_node.idx} -> st_node{st.idx} [color=grey dir=back]')
        self.current_table_node = st
        self.generic_visit(node)

        data = ''
        for item in itertools.chain(self.nodes, self.edges):
            data += f'{item}\n'

        st_data = '\n'.join(f'{node}' for node in self.symbol_table_nodes)

        return f'digraph G {{\nsubgraph cluster_st {{\n{st_data}}}\nnode [shape = rectangle]\n{data}}}'
