from graph import Graph
from visualizer import Visualizer

if __name__ == '__main__':
    # Inicializa o grafo vazio e passa para a interface visual
    # A escolha do algoritmo (Dijkstra ou A*) agora é feita diretamente na interface gráfica
    app = Visualizer(Graph())
    app.mainloop()