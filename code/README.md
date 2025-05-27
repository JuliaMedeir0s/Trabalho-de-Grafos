# Visualizador de Grafo GeoJSON

> 🚀 Um visualizador interativo de grafos georreferenciados, com zoom, pan e cálculo de menor caminho via Dijkstra.

---

## 📦 Estrutura do Projeto

```
├── index.html
├── src
│   ├── Node.js
│   ├── utils.js
│   ├── GrafoApp.js
│   └── main.js
└── README.md
```

- **index.html**  
  — HTML principal que carrega o canvas, input de arquivo e modal de confirmação (Bootstrap).  
- **src/Node.js**  
  — Classe `Node` que representa cada vértice do grafo.  
- **src/utils.js**  
  — Função `getRua(node)` para extrair o nome da rua de um nó.  
- **src/GrafoApp.js**  
  — Singleton com toda a lógica: carregamento GeoJSON, Dijkstra, renderização e eventos.  
- **src/main.js**  
  — Ponto de entrada que chama `GrafoApp.init()` após o carregamento do DOM.

---

## 🎯 Funcionalidades Principais

1. **Carregar GeoJSON**  
   - Selecione um arquivo `.geojson` contendo features de tipo LineString.  
   - O app converte coordenadas e constrói vértices e arestas.  

2. **Renderização no Canvas**  
   - Desenha todas as arestas (linhas cinza) e nós (círculos).  
   - Zoom com roda do mouse; pan (arrastar) com o botão esquerdo.  

3. **Seleção de Nós & Menor Caminho**  
   - Clique em um nó para escolher pontos inicial e final.  
   - Exibe um modal para confirmar a execução do algoritmo de Dijkstra.  
   - Traça o caminho encontrado em vermelho e destaca início (verde), fim (azul) e intermediários (amarelo).  
   - Exibe distância total e sequência de ruas utilizadas.  

4. **Mensagens de Status**  
   - Área “Distância” mostra passo a passo: carregamento, seleção e resultado.  
   - Área “Caminho” lista as ruas envolvidas no trajeto.

---

## 🎬 Como Usar

1. **Servir pela web**  
   ```bash
   # Com Python
   python3 -m http.server 8000
   # Ou com Node.js
   npm install -g serve
   serve .
   ```
2. Acesse no navegador:
   ```
   http://localhost:8000
   ```
3. Clique em **“Escolher arquivo”**, selecione seu GeoJSON.
4. Aguarde a mensagem **“Mapa carregado. Selecione o ponto inicial.”**
5. Clique no nó de partida, depois no nó de chegada.
6. Confirme no modal e veja o caminho desenhado!

---

## 🧩 Detalhes Internos

### 1. Classe `Node`
```js
class Node {
  constructor(lat, lon) {
    this.lat = lat;
    this.lon = lon;
    this.edges = [];  // conexões: { node, dist, rua }
  }
}
```

### 2. Carregamento GeoJSON
- Usa **FileReader** e **JSON.parse**.
- Itera por `features` de tipo **LineString**.
- Constrói um `Map<"lat,lon", Node>` para instâncias únicas.
- Calcula distância com método **haversine()**.

### 3. Dijkstra
```js
dijkstra(startNode, endNode) { … }
```
- Mapas `dist`, `prev` e `cameByRua`.
- Set como “fila” de prioridade (varredura linear).
- Reconstrói `path` e `ruas` ao final.

### 4. Canvas & Interações
- **project(lat,lon)** normaliza coordenadas ao retângulo do canvas.
- **drawGraph(path)**: limpa e redesenha arestas, nós e caminhos.
- Eventos de DOM:  
  - `click` → `handleClick`  
  - `wheel` → `handleZoom`  
  - `mousedown`/`mousemove`/`mouseup` → `startPan`/`doPan`  

---

## 💡 Dicas & Boas Práticas

- **Mantenha seu GeoJSON enxuto**: filtre apenas `LineString` de ruas/avenidas para melhor performance.  
- **Limites de zoom**: definidos entre `0.1x` e `20x` para evitar exageros.  
- **Customização visual**: ajuste cores ou tamanhos de nó/linha diretamente em `drawGraph()`.  
- **Extensibilidade**: você pode adicionar camadas de POIs ou labels explorando o mesmo padrão de desenho no canvas.

---

## 🤝 Contribuições

1. Fork este repositório.  
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`).  
3. Realize suas alterações e commit (`git commit -m 'Adiciona …'`).  
4. Abra um Pull Request para revisão.

---

## 📝 Licença

Este projeto está sob a [MIT License](LICENSE).

---

> Clique em 👍 se achou útil e compartilhe sugestões de melhoria!
