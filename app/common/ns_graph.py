# !/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
from networkx.drawing.nx_pydot import write_dot
from networkx.drawing.nx_pydot import read_dot
from collections import deque

from . import ns_datanalysis


class NsNode(Node):
    @property
    def alarm_pos(self):
        return self.__alarm_pos

    @alarm_pos.setter
    def alarm_pos(self, alarm_pos):
        self.__alarm_pos = alarm_pos

    @property
    def alarm_list(self):
        return self.__alarm_list

    @alarm_list.setter
    def alarm_list(self, alarm_list):
        self.__alarm_list = alarm_list
        self.alarm_pos = len(self.__alarm_list)

    def __init__(self, name=None, parent=None, alarm_list=None):
        super().__init__(name=name, parent=parent)
        self.__alarm_list = alarm_list
        self.__alarm_pos = len(self.__alarm_list)

    def __str__(self):
        return super().__str__() + str(self.alarm_list)

    def __repr__(self):
        return super().__repr__() + str(self.alarm_list)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name.__eq__(other.name)
        else:
            return None

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.name.__le__(other.name)
        else:
            return None

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.name.__lt__(other.name)
        else:
            return None

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.name.__ge__(other.name)
        else:
            return None

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.name.__gt__(other.name)
        else:
            return None

    def get_alarm(self):
        if self.alarm_pos < 1:
            return None
        self.alarm_pos -= 1
        return self.alarm_list[self.alarm_pos]


class NsGraph(nx.DiGraph):
    @property
    def name(self):
        return self.__name

    @property
    def link(self):
        return self.__link

    @link.setter
    def link(self, link_value):
        self.__link = link_value

    def __init__(self, name='topology', dot_file=None, link=None, path=None, graph=None):
        if graph:
            super().__init__(graph)
        else:
            super().__init__()
        self.__name = name
        if dot_file:
            self.load_graph(dot_file)
        elif isinstance(link, pd.DataFrame):
            self.__link = link
            self.init_graph()
        elif isinstance(path, pd.DataFrame):
            self.path_to_link(path)
            self.init_graph()

    def __str__(self):
        return self.__name + ':' + super().__str__()

    def __repr__(self):
        return self.__name + ':' + super().__repr__()

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name.__eq__(other.name)
        else:
            return None

    def init_graph(self):
        for i in range(len(self.link)):
             if (self.link.at[i, u'SRC_NE_ID'] == self.link.at[i, u'DST_NE_ID']) or \
                common.df_isna(self.link, i, u'SRC_NE_ID') or common.df_isna(self.link, i, u'DST_NE_ID'):
                continue
            if not self.has_node(self.link.at[i, 'SRC_NE_ID']):
                self.add_node(self.link.at[i, 'SRC_NE_ID'], type=self.link.at[i, 'SRC_NE_TYPE'])
            if not self.has_node(self.link.at[i, 'DST_NE_ID']):
                self.add_node(self.link.at[i, 'DST_NE_ID'], type=self.link.at[i, 'DST_NE_TYPE'])
            edge_type = 'single_domain' if self.link.at[i, 'SRC_NE_TYPE'] == self.link.at[i, 'DST_NE_TYPE']\
                else 'cross_domain'
            self.add_edge(self.link.at[i, 'SRC_NE_ID'], self.link.at[i, 'DST_NE_ID'], type=edge_type)

    def path_to_link(self, path=None):
        link_cols = ['SRC_NE_ID', 'SRC_NE_TYPE', 'DST_NE_ID', 'DST_NE_TYPE']
        link_list = []
        df_paths = path.groupby('PATH_ID', as_index=False)
        for path_name, cur_path in df_paths:
            prev_ne_id, prev_ne_type = None, None
            for row_index, row in cur_path.iterrows():
                cur_ne_id = cur_path.at[row_index, 'NE_NAME']
                cur_ne_type = cur_path.at[row_index, 'NE_TYPE']
                if prev_ne_id:
                    link_list.append([prev_ne_id, prev_ne_type, cur_ne_id, cur_ne_type])
                prev_ne_id, prev_ne_type = cur_ne_id, cur_ne_type
        self.__link = ns_datanalysis.df_from_matrix(link_list, link_cols)

    def load_graph(self, dot_file=None):
        if dot_file and os.path.isfile(dot_file):
            self.__init__(graph=nx.Graph(read_dot(dot_file)))
        else:
            print('ERROR: {} does not exists.'.format(dot_file))

    def get_node_type(self, n):
        return self.nodes[n]['type']

    def get_subgraph(self, nodes):
        return self.subgraph(nodes)

    def merge_graph(self, new_graph):
        self.add_nodes_from(new_graph.nodes(data=True))
        self.add_edges_from(new_graph.edges(data=True))

    def cycle_detect(self):
        result_list = []
        result_set = set()
        visited_set = set()
        for node in self.nodes():
            if node in visited_set:
                continue
            cur_visit_set = set()
            dfs_stack = deque()
            dfs_stack.append((node, []))
            while dfs_stack:
                cur_node, cur_path = dfs_stack.pop()
                cur_path.append(cur_node)
                cur_visit_set.add(cur_node)
                cur_path_set = set(cur_path)
                for x in self.neighbors(cur_node):
                    if x in cur_path_set:
                        cur_result = cur_path[cur_path.index(x):]
                        cur_result.append(x)
                        cur_result_set = frozenset(cur_result)
                        if cur_result_set not in result_set:
                            result_set.add(cur_result_set)
                            result_list.append(cur_result)
                    if x in visited_set:
                        continue
                    if x not in cur_path_set:
                        dfs_stack.append((x, cur_path[:]))
            visited_set.update(cur_visit_set)
        return result_list

    def save_dot(self, dot_file, layout=None):
        write_dot(self, dot_file)
        # layout enumerate: ['dot', 'neato', 'twopi', 'circo', 'fdp', 'sfdp']
        if layout:
            output_ext = 'pdf'
            img_file = ('.'.join(dot_file.split('.')[:-1])) + '_' + layout + '.' + output_ext
            os.system('{} {} -x -Goverlap=false -T {} -o {}'.format(layout, dot_file, output_ext, img_file))

    def show_graph(self, dot_file=None):
        if dot_file and os.path.isfile(dot_file):
            img_file = ('.'.join(dot_file.split('.')[:-1])) + '.png'
            if os.path.isfile(img_file):
                img = mpimg.imread(img_file)
                plt.imshow(img)
            else:
                print('ERROR: {0} does not exists.'.format(img_file))
                return
        else:
            pos = nx.nx_agraph.graphviz_layout(self)
            nx.draw(self, with_labels=True, pos=pos, node_color='blue')
        plt.axis('off')
        plt.show()


def __node_graph_test():
    # Tree test
    alarm_a = [1, 2, 3]
    alarm_b = [4, 5, 6]
    alarm_c = [7]
    a = NsNode('基站名称', parent=None, alarm_list=alarm_a)
    a1 = NsNode('基站名称', parent=None, alarm_list=alarm_a)
    a2 = a
    b = NsNode('b', parent=a, alarm_list=alarm_b)
    c = NsNode('c', parent=a, alarm_list=alarm_c)
    print(a is a1)
    print(a is a2)
    print(a == a1)
    print(a == a2)
    print(b == c)
    print(RenderTree(a))
    DotExporter(a).to_dotfile('tree.dot')
    # $dot tree.dot -T png -o tree.png

    # Graph test
    dot_file = 'topo1.dot'
    graph = read_dot(dot_file)
    pos = nx.nx_agraph.graphviz_layout(graph)
    print(pos)
    img_file = ('.'.join(dot_file.split('.')[:-1])) + '_fdp.png'
    dfp_cmd = 'fdp {} -T png -o {}'.format(dot_file, img_file)
    os.system(dfp_cmd)
    img = mpimg.imread(img_file)
    plt.imshow(img)
    plt.axis('off')
    plt.show()
    return


def graph_cycle_test():
    link_cols = [u'SRC_NE_ID', u'SRC_NE_TYPE', u'DST_NE_ID', u'DST_NE_TYPE']
    matrix = [[1, 'A', 2, 'A'], [2, 'A', 1, 'A'], [1, 'A', 3, 'A'], [3, 'A', 1, 'A'],
              [2, 'A', 3, 'A'], [3, 'A', 2, 'A'], [2, 'A', 4, 'B'], [5, 'B', 2, 'A'],
              [3, 'A', 6, 'B'], [6, 'B', 3, 'A'], [7, 'B', 3, 'A'], [4, 'A', 7, 'B'],
              [6, 'B', 5, 'B'], [6, 'B', 7, 'B']]
    df_rule = common.df_from_matrix(matrix, link_cols)

    g = NsGraph(link=df_rule)
    print(g.number_of_edges())
    # g.show_graph()
    # g.save_dot('alarm_rules_20190724.dot')
    import datetime
    print(str(datetime.datetime.now()))
    r = g.cycle_detect()
    print(r)
    print(str(datetime.datetime.now()))
