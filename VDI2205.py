import matplotlib.pyplot as plt
import numpy as np

# Crear la recta y = x en [0,1]
x = np.linspace(0, 1, 100)
y = x

plt.figure(figsize=(7,7))
plt.plot(x, y, label="y = x", color="blue", linewidth=2)

# Definir soluciones de ejemplo (puedes cambiarlas con tus valores reales)
soluciones = [
    (0.87, 0.89),  # Solución 1
    (0.80, 0.84),  # Solución 2
    (0.76, 0.68),  # Solsución 3
    (0.66, 0.73),  # Solución 4
]

# Graficar las soluciones con puntos más grandes
for i, (xi, ci) in enumerate(soluciones, start=1):
    plt.scatter(xi, ci, marker="o", s=150, label=f"Solución {i}")  # s = tamaño de punto
    plt.text(xi+0.015, ci, f"S{i}", fontsize=12, fontweight="bold")  # texto más grande y en negrita

# Configuración de ejes
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.xticks(np.arange(0, 1.1, 0.2), fontsize=12)
plt.yticks(np.arange(0, 1.1, 0.2), fontsize=12)

# Etiquetas y leyenda más grandes
plt.xlabel("Valor técnico Xᵢ", fontsize=14, fontweight="bold")
plt.ylabel("Valor económico Cᵢ", fontsize=14, fontweight="bold")
plt.title("Evaluación de soluciones según VDI 2225", fontsize=16, fontweight="bold")
plt.legend(fontsize=12)
plt.grid(True, linestyle="--", alpha=0.6)

plt.show()

# Función para calcular la distancia de un punto a la recta y = x
def distancia_a_recta_yx(punto):
    x, y = punto
    return abs(y - x) / np.sqrt(2)

# Calcular distancias para cada solución
distancias = [distancia_a_recta_yx(sol) for sol in soluciones]

# Encontrar la solución más óptima (la más cercana a la recta)
indice_optimo = np.argmin(distancias)
solucion_optima = soluciones[indice_optimo]
distancia_optima = distancias[indice_optimo]

# Mostrar resultados
for i, (sol, dist) in enumerate(zip(soluciones, distancias), start=1):
    print(f"Solución {i}: {sol}, Distancia = {dist:.4f}")

print("\nLa solución más óptima es:")
print(f"Solución {indice_optimo+1}: {solucion_optima} con distancia {distancia_optima:.4f}")