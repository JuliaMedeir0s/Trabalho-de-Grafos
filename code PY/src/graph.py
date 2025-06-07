import heapq
import math
from typing import Dict, List, Tuple

# Constante para o raio da Terra em metros
RAIO_TERRA_M = 6371000

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância em metros entre duas coordenadas lat/lon usando a fórmula de Haversine."""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    rad_lat1 = math.radians(lat1)
    rad_lat2 = math.radians(lat2)
    
    a = (math.sin(d_lat / 2) ** 2) + (math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return RAIO_TERRA_M * c

class Node:
    def __init__(self, id: str, x: float, y: float):
        self.id = id
        self.x = x  # Longitude
        self.y = y  # Latitude
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
        if src_id in self.nodes and dst_id in self.nodes:
            src = self.nodes[src_id]
            dst = self.nodes[dst_id]
            src.add_edge(dst, w, name)
            dst.add_edge(src, w, name)

    # VERSÃO OTIMIZADA do Dijkstra com Fila de Prioridade (heap)
    def _dijkstra(self, start_id: str) -> Tuple[Dict[str, float], Dict[str, str]]:
        dist = {nid: math.inf for nid in self.nodes}
        prev: Dict[str, str] = {}
        dist[start_id] = 0
        
        # Fila de prioridade: (distância, node_id)
        pq = [(0, start_id)]

        while pq:
            d, u_id = heapq.heappop(pq)

            # Se já encontramos um caminho menor, ignoramos este
            if d > dist[u_id]:
                continue

            u_node = self.nodes[u_id]
            for v_node, w, _ in u_node.edges:
                if dist[u_id] + w < dist[v_node.id]:
                    dist[v_node.id] = dist[u_id] + w
                    prev[v_node.id] = u_id
                    heapq.heappush(pq, (dist[v_node.id], v_node.id))
                    
        return dist, prev
    
    def _heuristic(self, node_id1: str, node_id2: str) -> float:
        """Heurística para A* usando a distância de Haversine."""
        node1 = self.nodes[node_id1]
        node2 = self.nodes[node_id2]
        return haversine_distance(node1.y, node1.x, node2.y, node2.x)

    # A* já é eficiente, apenas garantimos que a heurística seja boa
    def _astar_prev(self, start_id: str, end_id: str) -> Dict[str, str]:
        open_set = {start_id}
        came_from: Dict[str, str] = {}
        
        g_score = {nid: math.inf for nid in self.nodes}
        g_score[start_id] = 0
        
        f_score = {nid: math.inf for nid in self.nodes}
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
        prev = {}
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
        if not p1: return [], []

        removed_edges = []
        for u, v, w, name in p1:
            self.nodes[u.id].edges = [e for e in self.nodes[u.id].edges if not (e[0].id == v.id and e[1] == w)]
            self.nodes[v.id].edges = [e for e in self.nodes[v.id].edges if not (e[0].id == u.id and e[1] == w)]
            removed_edges.append((u.id, v.id, w, name))

        p2 = self.shortest_path(start_id, end_id, method)

        for u_id, v_id, w, name in removed_edges:
            self.add_edge(u_id, v_id, w, name)
            
        return p1, p2