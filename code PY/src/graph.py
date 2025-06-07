from typing import Dict, List, Tuple
import math

class Node:
    def __init__(self, id: str, x: float, y: float):
        self.id = id
        self.x = x
        self.y = y
        self.edges: List[Tuple['Node', float, str]] = []

    def add_edge(self, dest: 'Node', weight: float, name: str):
        self.edges.append((dest, weight, name))

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def add_node(self, id: str, x: float, y: float):
        if id not in self.nodes:
            self.nodes[id] = Node(id, x, y)

    def add_edge(self, src_id: str, dst_id: str, w: float, name: str = ""):
        src = self.nodes[src_id]
        dst = self.nodes[dst_id]
        src.add_edge(dst, w, name)
        dst.add_edge(src, w, name)

    def _dijkstra(self, start_id: str) -> Tuple[Dict[str, float], Dict[str, str]]:
        dist = {nid: math.inf for nid in self.nodes}
        prev: Dict[str, str] = {}
        dist[start_id] = 0
        Q = set(self.nodes.keys())

        while Q:
            u = min(Q, key=lambda nid: dist[nid])
            Q.remove(u)
            for v, w, _ in self.nodes[u].edges:
                alt = dist[u] + w
                if alt < dist[v.id]:
                    dist[v.id] = alt
                    prev[v.id] = u
        return dist, prev

    def _astar_prev(self, start_id: str, end_id: str) -> Dict[str, str]:
        open_set = {start_id}
        came_from: Dict[str, str] = {}
        g_score = {nid: math.inf for nid in self.nodes}
        f_score = {nid: math.inf for nid in self.nodes}
        g_score[start_id] = 0
        f_score[start_id] = self._heuristic(start_id, end_id)

        while open_set:
            current = min(open_set, key=lambda nid: f_score[nid])
            if current == end_id:
                return came_from
            open_set.remove(current)
            for neighbor, w, _ in self.nodes[current].edges:
                tentative_g = g_score[current] + w
                if tentative_g < g_score[neighbor.id]:
                    came_from[neighbor.id] = current
                    g_score[neighbor.id] = tentative_g
                    f_score[neighbor.id] = tentative_g + self._heuristic(neighbor.id, end_id)
                    if neighbor.id not in open_set:
                        open_set.add(neighbor.id)
        return came_from

    def shortest_path(self, start_id: str, end_id: str, method: str) -> List[Tuple[Node, Node, float, str]]:
        if method.upper() == 'D':
            _, prev = self._dijkstra(start_id)
        else:
            prev = self._astar_prev(start_id, end_id)

        path = []
        u = end_id
        while u in prev:
            p = prev[u]
            for dest, w, name in self.nodes[p].edges:
                if dest.id == u:
                    path.insert(0, (self.nodes[p], dest, w, name))
                    break
            u = p
        return path

    def shortest_two_paths(self, start_id: str, end_id: str, method: str) -> Tuple[List, List]:
        p1 = self.shortest_path(start_id, end_id, method)
        removed = []
        for u, v, w, name in p1:
            self.nodes[u.id].edges = [e for e in self.nodes[u.id].edges if not (e[0].id == v.id and e[1] == w and e[2] == name)]
            self.nodes[v.id].edges = [e for e in self.nodes[v.id].edges if not (e[0].id == u.id and e[1] == w and e[2] == name)]
            removed.append((u.id, v.id, w, name))
        p2 = self.shortest_path(start_id, end_id, method)
        for u_id, v_id, w, name in removed:
            self.add_edge(u_id, v_id, w, name)
        return p1, p2
