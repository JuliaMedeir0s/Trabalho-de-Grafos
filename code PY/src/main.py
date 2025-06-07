from graph import Graph
from visualizer import Visualizer

if __name__ == '__main__':
    # A seleção do método foi movida para a interface do Visualizer
    app = Visualizer(Graph())
    app.mainloop()