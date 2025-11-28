import matplotlib.pyplot as plt
import numpy as np
import json
# Ejemplo de datos de 1 hora dividido en intervalos de 10 minutos 
time_intervals = np.arange(0, 61, 10) 
json_file_name = "resultados_total.json"
total_file = None
def get_difference(json_file):
    global total_file
    final_result = []
    last_value = 0
    with open(json_file, "r") as file:
      data = json.load(file)
      if json_file == json_file_name:
         total_file=data
      
      for key,value in data.items():
         if int(key) == 10:
            final_result.append(int(value))
         else:
      
            final_result.append(int(value)-int(last_value))
         last_value = value
    return final_result


    
def get_final_result(differences_list, total_list_difference):
   result = []
   for i in range(len(total_list_difference)):
      result.append(total_list_difference[i]-differences_list[i])
   return result



total_alarms_raw = get_difference("resultados_total.json")   # alarmas brutas
primer_valor = [0]
processed_alarms = [0] + get_final_result(
    get_difference("resultados_middleware.json"),
    total_alarms_raw
)
processed_alarms_n2v = [0] + get_final_result(
    get_difference("resultados_middleware_n2v.json"),
    total_alarms_raw
)
processed_alarms_fuzzy = [0] + get_final_result(
    get_difference("resultados_middleware_fuzzy.json"),
    total_alarms_raw
)

total_alarms = [0] + total_alarms_raw
print(total_alarms)
print(processed_alarms)
print(processed_alarms_n2v)
print(processed_alarms_fuzzy)
# Línea de referencia EEMUA: 1 alarma por 10 minutos
eemua_ref = [1] * len(time_intervals)

plt.figure(figsize=(10,6))
plt.plot(time_intervals, total_alarms, marker='o', color='blue', label="Alarmas totales (crudas)")
plt.plot(time_intervals, processed_alarms, marker='o', color='green', label="Alarmas luego de middleware")
plt.plot(time_intervals, processed_alarms_n2v, marker='o', color='purple', label="Alarmas luego de clustering n2v")
plt.plot(time_intervals, processed_alarms_fuzzy, marker='o', color='orange', label="Alarmas luego de clustering fuzzy")
plt.plot(time_intervals, eemua_ref, linestyle="--", color='red', label="Referencia EEMUA (1 alarma/10min)")



plt.title("Comparación de alarmas vs EEMUA (1 hora)")
plt.xlabel("Tiempo (minutos)")
plt.ylabel("Número de alarmas cada 10 min")
plt.xticks(time_intervals) 
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()