import matplotlib.pyplot as plt
import numpy as np

# Ejemplo de datos de 1 hora dividido en intervalos de 10 minutos 
time_intervals = np.arange(0, 61, 10)  

# Datos simulados: remplaza con tus conteos reales
total_alarms = [0,9, 6, 7, 23, 7, 7]   # alarmas brutas
processed_alarms = [0,4, 1, 1, 6, 2, 1]  # luego middleware

# Línea de referencia EEMUA: 1 alarma por 10 minutos
eemua_ref = [1] * len(time_intervals)

plt.figure(figsize=(10,6))
plt.plot(time_intervals, total_alarms, marker='o', color='blue', label="Alarmas totales (crudas)")
plt.plot(time_intervals, processed_alarms, marker='o', color='green', label="Alarmas luego de middleware")
plt.plot(time_intervals, eemua_ref, linestyle="--", color='red', label="Referencia EEMUA (1 alarma/10min)")
plt.axvline(x=10, color='purple', linestyle='--', linewidth=2)
plt.axvline(x=40, color='purple', linestyle='--', linewidth=2)


plt.title("Comparación de alarmas vs EEMUA (1 hora)")
plt.xlabel("Tiempo (minutos)")
plt.ylabel("Número de alarmas cada 10 min")
plt.xticks(time_intervals)  # marcas cada 10 minutos
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()