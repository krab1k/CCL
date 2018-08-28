import itertools
import html

from ccl_ast import *


class GraphNode:
    def __init__(self, idx: int, node_type: str):
        self.idx: int = idx
        self.node_type: str = node_type
        self.properties: List[str] = []

    def __str__(self):
        property_string = '<br/>'.join(prop for prop in self.properties)
        return f'node{self.idx} [label = < <b>{self.node_type}</b><br/> {property_string} >]'


class Generator(ASTVisitor):
    def __init__(self):
        super().__init__()
        self.nodes: List[GraphNode] = []
        self.edges: List[str] = []
        gn = GraphNode(0, 'Method')
        self.nodes.append(gn)
        self.current_node: GraphNode = gn

    def _visit(self, field, node):
        gn = GraphNode(len(self.nodes) + 1, node.__class__.__name__)
        self.nodes.append(gn)
        self.edges.append(f'node{self.current_node.idx} -> node{gn.idx} [label = "{field}"]')
        old = self.current_node
        self.current_node = gn
        self.visit(node)
        self.current_node = old

    def generic_visit(self, node: ASTNode):
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

    def output(self, ast: Method):
        self.visit(ast)
        data = ''
        for item in itertools.chain(self.nodes, self.edges):
            data += f'{item}\n'

        return f'digraph G {{\nnode [shape=rectangle]\n{data}}}'
