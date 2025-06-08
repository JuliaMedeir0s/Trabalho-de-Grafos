import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import math
import time
from graph import Graph, haversine_distance

class Visualizer(tk.Tk):
    def __init__(self, graph: Graph):
        super().__init__()
        self.title("Roteamento Urbano")
        self.geometry("1100x700")

        # Variáveis para armazenar grafo e seleções de origem/destino
        self.graph = graph
        self.start_id = None
        self.end_id = None
        self.path1 = None
        self.path2 = None

        # Frame principal: divide entre área de desenho (canvas) e sidebar de controles
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas: área onde o grafo será desenhado
        self.canvas = tk.Canvas(main_frame, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sidebar: área com botões, informações e controles
        sidebar = ttk.Frame(main_frame, width=300, padding="10")
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Status de carregamento e instruções
        status_header = ttk.Label(sidebar, text="Status", font=("TkDefaultFont", 12, "bold"))
        status_header.pack(pady=(0, 5), anchor='w')
        self.status_label = ttk.Label(sidebar, text="Carregue um arquivo GeoJSON.", wraplength=280)
        self.status_label.pack(pady=5, anchor='w', fill=tk.X)

        # Exibição de informações do grafo (número de nós e arestas)
        self.graph_info_label = ttk.Label(sidebar, text="Informações do Grafo", font=("TkDefaultFont", 10, "bold"))
        self.graph_info_label.pack(anchor='w', pady=(10,0))
        self.nodes_label = ttk.Label(sidebar, text="Nós (Vértices): -")
        self.nodes_label.pack(anchor='w')
        self.edges_label = ttk.Label(sidebar, text="Arestas: -")
        self.edges_label.pack(anchor='w')

        # Botão para resetar seleções de origem/destino
        reset_button = ttk.Button(sidebar, text="Resetar Seleção", command=self._reset_selection)
        reset_button.pack(fill=tk.X, pady=10)

        ttk.Separator(sidebar, orient='horizontal').pack(fill='x', pady=5)

        # Escolha do algoritmo (Dijkstra ou A*)
        algo_header = ttk.Label(sidebar, text="Algoritmo", font=("TkDefaultFont", 10, "bold"))
        algo_header.pack(anchor='w')
        self.method_var = tk.StringVar(value='D')
        dijkstra_rb = ttk.Radiobutton(sidebar, text="Dijkstra (Otimizado)", variable=self.method_var, value='D')
        dijkstra_rb.pack(anchor='w')
        astar_rb = ttk.Radiobutton(sidebar, text="A* (A-Star)", variable=self.method_var, value='A')
        astar_rb.pack(anchor='w')

        # Label para exibir o tempo de execução da busca
        self.time_label = ttk.Label(sidebar, text="Tempo de Execução: -", font=("TkDefaultFont", 9, "italic"))
        self.time_label.pack(pady=(5,0), anchor='w')

        ttk.Separator(sidebar, orient='horizontal').pack(fill='x', pady=10)

        # Exibição dos detalhes do primeiro caminho encontrado
        path1_header = ttk.Label(sidebar, text="Caminho 1 (Vermelho)", font=("TkDefaultFont", 10, "bold"))
        path1_header.pack(anchor='w')
        self.path1_details = ttk.Label(sidebar, text="-", wraplength=280, justify=tk.LEFT)
        self.path1_details.pack(pady=(5, 15), anchor='w', fill=tk.X)

        # Exibição dos detalhes do segundo caminho encontrado
        path2_header = ttk.Label(sidebar, text="Caminho 2 (Azul)", font=("TkDefaultFont", 10, "bold"))
        path2_header.pack(anchor='w')
        self.path2_details = ttk.Label(sidebar, text="-", wraplength=280, justify=tk.LEFT)
        self.path2_details.pack(pady=5, anchor='w', fill=tk.X)

        # Variáveis de controle para zoom e movimentação no canvas
        self.margin, self.scale = 20, 1.0
        self.offset_x, self.offset_y = 0, 0
        self._pan_start = None

        # Bind de eventos do mouse para zoom, pan e seleção
        self.canvas.bind('<ButtonPress-3>', self._on_pan_start)     # Botão direito: iniciar movimentação
        self.canvas.bind('<B3-Motion>', self._on_pan_move)          # Botão direito + mover: movimentar canvas
        self.canvas.bind('<MouseWheel>', self._on_zoom)             # Scroll do mouse: zoom
        self.canvas.bind('<ButtonPress-1>', self._on_click)         # Botão esquerdo: selecionar nós

        # Chama função para carregar grafo ao iniciar
        self._load_graph_from_file()

    def _load_graph_from_file(self):
        """
        Abre uma janela para o usuário selecionar o arquivo GeoJSON, 
        lê os dados e popula o grafo com nós e arestas.
        """
        path = filedialog.askopenfilename(title="Selecione GeoJSON", filetypes=[("GeoJSON", "*.geojson *.json")])
        if not path:
            self.destroy()
            return

        t0 = time.perf_counter() # Tempo inicial para medir performance
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Para cada feature no GeoJSON, extrai ruas e pontos
        for feat in data['features']:
            geometry = feat.get('geometry')
            if not geometry:
                continue

            street = feat['properties'].get('name', '')
            geom_type = geometry.get('type')
            coords = geometry.get('coordinates')
            
            # Lista que conterá os pontos a serem processados
            points_to_process = []

            # Trata tanto LineString quanto Polygon
            if geom_type == 'LineString':
                points_to_process = coords
            elif geom_type == 'Polygon':
                # Para polígonos, as coordenadas são uma lista de anéis.
                # Usamos apenas o primeiro anel (o contorno externo).
                if coords and len(coords) > 0:
                    points_to_process = coords[0]
            
            # Se não for um tipo de geometria que sabemos tratar, pulamos para a próxima feature
            if not points_to_process:
                continue

            # Agora o processamento é seguro, pois points_to_process é uma lista simples de pontos
            for lon, lat in points_to_process:
                self.graph.add_node(str((lon, lat)), lon, lat)
            
            # Cria arestas entre pontos consecutivos
            for i in range(len(points_to_process) - 1):
                u_lon, u_lat = points_to_process[i]
                v_lon, v_lat = points_to_process[i+1]
                w = haversine_distance(u_lat, u_lon, v_lat, v_lon)
                self.graph.add_edge(str((u_lon, u_lat)), str((v_lon, v_lat)), w, street)
        
        # Exibe tempo de carregamento e informações básicas
        load_time = (time.perf_counter() - t0) * 1000
        self.status_label.config(text=f"Grafo processado em {load_time:.2f} ms.\nSelecione o ponto inicial.")

        num_nodes = len(self.graph.nodes)
        num_edges = sum(len(n.edges) for n in self.graph.nodes.values()) // 2
        self.nodes_label.config(text=f"Nós (Vértices): {num_nodes}")
        self.edges_label.config(text=f"Arestas: {num_edges}")

        # Calcula limites geográficos para ajustar zoom e proporção
        xs = [n.x for n in self.graph.nodes.values()]
        ys = [n.y for n in self.graph.nodes.values()]
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)

        # Define escala de zoom inicial
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        w_geo, h_geo = self.max_x - self.min_x or 1, self.max_y - self.min_y or 1
        scale_x = (canvas_width - 2 * self.margin) / w_geo
        scale_y = (canvas_height - 2 * self.margin) / h_geo
        self.scale = min(scale_x, scale_y)
        self._redraw()

    def _on_click(self, event):
        """
        Evento de clique do mouse: seleciona o nó mais próximo.
        Se for o primeiro clique, define como ponto de partida;
        Se for o segundo, define como destino e executa busca pelo(s) melhor(es) caminho(s).
        """
        closest, min_d = None, math.inf
        for nid, n in self.graph.nodes.items():
            sx, sy = self.world_to_screen(n.x, n.y)
            d = (sx - event.x)**2 + (sy - event.y)**2
            if d < min_d:
                min_d, closest = d, nid
        
        if not self.start_id:
            # Primeiro clique: seleciona ponto inicial
            self.start_id = closest
            self.status_label.config(text="Ponto inicial selecionado.\nSelecione o ponto final.")
            self._redraw()
        else:
            # Segundo clique: seleciona ponto final e executa algoritmo escolhido
            self.end_id = closest
            if messagebox.askyesno("Confirmar Rota", "Deseja encontrar o menor caminho?"):
                
                t_start = time.perf_counter()
                selected_method = self.method_var.get()
                p1, p2 = self.graph.shortest_two_paths(self.start_id, self.end_id, selected_method)
                t_end = time.perf_counter()
                
                self.path1, self.path2 = p1, p2
                exec_time_ms = (t_end - t_start) * 1000
                self.time_label.config(text=f"Tempo de Execução: {exec_time_ms:.2f} ms")

                # Função auxiliar para resumir distância e ruas do caminho
                def summarize(path):
                    if not path: return 0.0, ["N/A"]
                    dist = sum(w for _, _, w, _ in path)
                    ruas = list(dict.fromkeys([name for _, _, _, name in path if name]))
                    return dist, ruas if ruas else ["Trecho desconhecido"]

                d1, r1 = summarize(p1)
                d2, r2 = summarize(p2)
                
                dist_km1, dist_km2 = d1 / 1000, d2 / 1000
                
                self.status_label.config(text="Caminhos calculados!")
                self.path1_details.config(text=f"Distância: {dist_km1:.2f} km\nRuas: {', '.join(r1)}")
                self.path2_details.config(text=f"Distância: {dist_km2:.2f} km\nRuas: {', '.join(r2)}")

                self._redraw()
                self.start_id, self.end_id = None, None
            else:
                # Se cancelar, volta para seleção do destino
                self.end_id = None
                self.status_label.config(text="Seleção do ponto final cancelada.")
                self._redraw()

    def world_to_screen(self, lon, lat):
        """
        Converte coordenadas geográficas para coordenadas de tela (canvas).
        Ajusta escala e deslocamento para garantir zoom e pan.
        """
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        x = (lon - self.min_x) * self.scale + self.margin + self.offset_x
        y = canvas_height - ((lat - self.min_y) * self.scale + self.margin) - self.offset_y
        return x, y

    def _redraw(self):
        """
        Redesenha todo o grafo no canvas, incluindo nós, arestas e os caminhos destacados.
        """
        self.canvas.delete('all')
        
        # Coleta os nós envolvidos nos caminhos para destacar
        path1_nodes = {n.id for segment in (self.path1 or []) for n in (segment[0], segment[1])}
        path2_nodes = {n.id for segment in (self.path2 or []) for n in (segment[0], segment[1])}
        
        # Desenha todas as arestas (ruas) em cinza claro
        for u in self.graph.nodes.values():
            x1, y1 = self.world_to_screen(u.x, u.y)
            for v, _, _ in u.edges:
                x2, y2 = self.world_to_screen(v.x, v.y)
                self.canvas.create_line(x1, y1, x2, y2, fill='lightgray')

        # Desenha os nós, destacando início, fim e caminhos
        for u_id, u_node in self.graph.nodes.items():
            x, y = self.world_to_screen(u_node.x, u_node.y)
            radius, color = 3, 'black'

            if u_id == self.start_id:
                radius, color = 7, '#28a745'    # Verde: ponto inicial
            elif u_id == self.end_id:
                radius, color = 7, '#007bff'    # Azul: ponto final
            elif u_id in path1_nodes or u_id in path2_nodes:
                radius, color = 4, '#ffc107'    # Amarelo: nó do caminho

            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline='white')
        
        # Desenha os caminhos encontrados: 1 (vermelho), 2 (azul)
        if self.path1: self._draw_path(self.path1, 'red')
        if self.path2: self._draw_path(self.path2, 'blue')
        
    def _draw_path(self, path, color):
        """
        Desenha um caminho destacado no canvas, na cor especificada.
        """
        for u, v, _, _ in path:
            x1, y1 = self.world_to_screen(u.x, u.y)
            x2, y2 = self.world_to_screen(v.x, v.y)
            self.canvas.create_line(x1, y1, x2, y2, width=3, fill=color)

    def _reset_selection(self):
        """
        Reseta seleção dos pontos de início/fim e dos caminhos exibidos.
        """
        self.start_id, self.end_id = None, None
        self.path1, self.path2 = None, None
        self.status_label.config(text="Seleção resetada. Escolha um ponto de início.")
        self.path1_details.config(text="-")
        self.path2_details.config(text="-")
        self.time_label.config(text="Tempo de Execução: -")
        self._redraw()

    def _on_pan_start(self, event):
        """
        Evento: início do movimento do canvas (pan).
        """
        self._pan_start = (event.x, event.y)

    def _on_pan_move(self, event):
        """
        Evento: movimentação do canvas enquanto o botão do mouse está pressionado.
        """
        if self._pan_start:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self.offset_x += dx
            self.offset_y += dy
            self._pan_start = (event.x, event.y)
            self._redraw()

    def _on_zoom(self, event):
        """
        Evento: zoom in/out no canvas usando o scroll do mouse.
        """
        factor = 1.0 + (event.delta / 1200)
        old_scale = self.scale
        self.scale *= factor
        
        cx, cy = event.x, event.y
        self.offset_x = cx - (cx - self.offset_x) * (self.scale / old_scale)
        self.offset_y = cy - (cy - self.offset_y) * (self.scale / old_scale)
        self._redraw()