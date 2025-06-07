from graph import Graph
from visualizer import Visualizer

if __name__ == '__main__':
    method = input("Método [D]ijkstra (D) ou A* (A): ").strip().upper()
    if method not in ('D', 'A'):
        method = 'D'
    app = Visualizer(Graph(), method)
    app.mainloop()
