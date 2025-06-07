import tkinter as tk
from tkinter import filedialog
import json, math, time
from graph import Graph

class Visualizer(tk.Tk):
    def __init__(self, graph: Graph, method: str):
        super().__init__()
        self.title("Roteamento Urbano")
        self.width, self.height, self.margin = 800, 600, 20
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.graph = graph
        self.method = method
        self.start_id = None
        self.end_id = None

        # Transformações de visualização
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._pan_start = None

        # Eventos para zoom e pan
        self.canvas.bind('<ButtonPress-3>', self._on_pan_start)
        self.canvas.bind('<B3-Motion>', self._on_pan_move)
        self.canvas.bind('<MouseWheel>', self._on_zoom)

        # Seleção de GeoJSON
        path = filedialog.askopenfilename(title="Selecione GeoJSON", filetypes=[("GeoJSON","*.geojson *.json")])
        if not path:
            return self.destroy()

        # Carrega e processa grafo
        t0 = time.perf_counter()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for feat in data['features']:
            street = feat['properties'].get('name', '')
            coords = feat['geometry']['coordinates']
            for lon, lat in coords:
                self.graph.add_node(str((lon,lat)), lon, lat)
            for i in range(len(coords)-1):
                u, v = tuple(coords[i]), tuple(coords[i+1])
                w = math.hypot(v[0]-u[0], v[1]-u[1])
                self.graph.add_edge(str(u), str(v), w, street)
        load_time = (time.perf_counter() - t0) * 1000
        print(f"Processou grafo em {load_time:.2f} ms")

        # Calcula bounding box
        xs = [n.x for n in self.graph.nodes.values()]
        ys = [n.y for n in self.graph.nodes.values()]
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)

        # Ajuste de escala inicial
        w_geo = self.max_x - self.min_x or 1
        h_geo = self.max_y - self.min_y or 1
        scale_x = (self.width - 2*self.margin) / w_geo
        scale_y = (self.height - 2*self.margin) / h_geo
        self.scale = min(scale_x, scale_y)

        # Desenha inicial
        self._redraw()
        # Eventos para seleção de rota
        self.canvas.bind('<ButtonPress-1>', self._on_click)

    def world_to_screen(self, lon, lat):
        # Converte coordenadas geo -> canvas com escala e offset
        x = (lon - self.min_x) * self.scale + self.margin + self.offset_x
        y = self.height - ((lat - self.min_y) * self.scale + self.margin) + self.offset_y
        return x, y

    def _redraw(self):
        self.canvas.delete('all')
        # Desenha arestas
        for u in self.graph.nodes.values():
            x1, y1 = self.world_to_screen(u.x, u.y)
            for v, _, _ in u.edges:
                x2, y2 = self.world_to_screen(v.x, v.y)
                self.canvas.create_line(x1, y1, x2, y2, fill='gray')
        # Desenha nós
        for u in self.graph.nodes.values():
            x, y = self.world_to_screen(u.x, u.y)
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='black')

    def _on_pan_start(self, event):
        self._pan_start = (event.x, event.y)

    def _on_pan_move(self, event):
        if self._pan_start:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self._pan_start = (event.x, event.y)
            self._redraw()

    def _on_zoom(self, event):
        # Zoom centralizado no cursor
        factor = 1.0 + (event.delta / 1200)
        old_scale = self.scale
        self.scale *= factor
        # Ajustar offset para manter ponto sob cursor
        cx, cy = event.x, event.y
        self.offset_x = cx - (cx - self.offset_x) * (self.scale / old_scale)
        self.offset_y = cy - (cy - self.offset_y) * (self.scale / old_scale)
        self._redraw()

    def _on_click(self, event):
        # Seleciona nós e desenha rotas (mantém lógica de dois caminhos)
        # (mesma lógica de antes, usando self.world_to_screen)
        closest, min_d = None, math.inf
        for nid, n in self.graph.nodes.items():
            sx, sy = self.world_to_screen(n.x, n.y)
            d = (sx-event.x)**2 + (sy-event.y)**2
            if d < min_d:
                min_d, closest = d, nid
        if not self.start_id:
            self.start_id = closest
            print(f"Start: {closest}")
        else:
            self.end_id = closest
            print(f"End: {closest}")
            p1, p2 = self.graph.shortest_two_paths(self.start_id, self.end_id, self.method)
            def summarize(path):
                dist = sum(w for _, _, w, _ in path)
                ruas = [name for _, _, _, name in path]
                return dist, ruas
            d1, r1 = summarize(p1)
            d2, r2 = summarize(p2)
            print(f"C1: {d1:.2f}m, {r1}")
            print(f"C2: {d2:.2f}m, {r2}")
            # Redesenha e destaca caminhos
            self._redraw()
            for path, color in ((p1,'red'), (p2,'blue')):
                for u, v, _, _ in path:
                    x1, y1 = self.world_to_screen(u.x, u.y)
                    x2, y2 = self.world_to_screen(v.x, v.y)
                    self.canvas.create_line(x1, y1, x2, y2, width=3, fill=color)
            self.canvas.create_text(self.width/2, 10, text=f"C1={d1:.1f}m C2={d2:.1f}m", fill='black')
            # Resetar seleção
            self.start_id = None
            self.end_id = None