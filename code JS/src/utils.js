export function getRua(node) {
  if (node && node.edges && node.edges.length > 0) {
    for (const edge of node.edges) {
      if (edge.rua && edge.rua !== "Rua desconhecida") {
        return edge.rua;
      }
    }
    return node.edges[0].rua || "Rua desconhecida";
  }
  return "Localização desconhecida";
}
