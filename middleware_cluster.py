import asyncio
from panoramisk.manager import Manager
from operator import itemgetter
from pymodbus.client import AsyncModbusTcpClient
import json

import time
# AMI (puede quedarse global porque panoramisk crea su loop internamente)
manager = Manager(
    host='192.168.0.16',  # Asterisk AMI
    port=5038,
    username='amiuser',
    secret='luis'
)

# Asterisk Actions
actions = {
    "action_playback": {
        "Action": "Originate",
        "Channel": "PJSIP/mantenimiento_electrico",
        "Context": "internal",
        "Exten": "1002",
        "Priority": "1",
        "CallerID": "Middleware <1000>",
        "Timeout": "30000",
        "Async": "true",
        "Application": "Playback",
        "Data": "es/custom/alarma-8k"
    },
    "action_message" : {
        "Action": "MessageSend",
        "To": "PJSIP/mantenimiento_electrico",  
        "From": "<Middleware>",       
        "Body": None
    }
}

# Cargamos los df de los resultados
import pandas as pd
cluster_n2v = pd.read_csv("alarm_n2v_clusters.csv")
cluster_fuzzy = pd.read_csv("alarm_clusters.csv")

## Funcion N2Vec + K means Clustering
def get_cluster_n2v(tag):
    fila = cluster_n2v[cluster_n2v["tag"] == tag]
    if not fila.empty:
        cluster = fila["cluster"].iloc[0]  # obtener el valor de la fila
        return cluster
    else:
        print("Alarma no encontrada (posiblemente nueva)")
        return None
target_n2v_cluster = 0

## Funcion Fuzzy Clustering
def get_cluster_fuzzy(tag):
    fila = cluster_fuzzy[cluster_fuzzy["tag"] == tag]
    
    if not fila.empty:
        cluster_name = fila["cluster_fuzzy"].iloc[0]  # obtener el valor de la fila
        if cluster_name == "μ_cluster_1":
            return 1
        else:
            return 0
    else:
        print("Alarma no encontrada (posiblemente nueva)")
        return None
target_fuzzy_cluster = 1


# Alarm states
alarm_states = {}
count_alarms = 0
count_alarms_fuzzy = 0
count_alarms_n2v = 0
result_dict = {"10":None,"20":None,"30": None,"40": None,"50":None,"60":None}
result_dict_fuzzy = {"10":None,"20":None,"30": None,"40": None,"50":None,"60":None}
result_dict_n2v = {"10":None,"20":None,"30": None,"40": None,"50":None,"60":None}
minutes = time.time()
async def trigger_action(severity, message, data, tag):
    global count_alarms
    

    count_alarms +=1
    response = await manager.send_action(actions["action_playback"])

    # Enviar mensaje SIP SIMPLE
    action_message= actions["action_message"]
    action_message["Body"] = f" Alarma: {tag}\nNivel: {severity}\nMensaje: {message}\nValor actual: {data}"
    response_msg = await manager.send_action(action_message)


def check_and_update_alarm(policy, value):
    tag = policy["tag"]
    need_action = False
    prev_state = alarm_states.get(tag, {"active": False})
    is_state_active = prev_state["active"]
    value = int(value)
    
    if policy.get("limits"):
        low, high = policy["limits"].get("low"), policy["limits"].get("high")
        need_action = (low is not None and value <= low) or (high is not None and value >= high)
    else:
        need_action = int(policy["condition"][-1]) == value
    if need_action and not is_state_active:
        alarm_states[tag] = {"active": True, "value": value}
        return True
    elif not need_action and is_state_active:
        alarm_states[tag] = {"active": False, "value": value}
    else:
        if alarm_states.get(tag):
            alarm_states[tag]["value"] = value
    return False

async def apply_plan_policy(hr, di, co, ir):

    global count_alarms_n2v
    global count_alarms_fuzzy
    selected_severities = ["Critico"]
    registers_dictionary = {
        "HR": hr.registers if hasattr(hr, "registers") else [],
        "DI": di.bits if hasattr(di, "bits") else [],
        "CO": co.bits if hasattr(co, "bits") else [],
        "IR": ir.registers if hasattr(ir, "registers") else []
    }
    with open("alarm_config.json", "r", encoding="utf-8") as file:
        policies = json.load(file)

    for policy in policies:
        policy_type = policy["source"]["type"]
        register = registers_dictionary.get(policy_type, [])
        if not register:
            continue
        data_register = register[policy["source"]["address"]]
        tag, severity, message = itemgetter("tag", "severity", "message")(policy)
        trigger_alarm = check_and_update_alarm(policy, data_register)
        
        ### Logica Clusters
        if trigger_alarm:
            print("Triggered" + tag)
            print(get_cluster_fuzzy(tag))
            print(get_cluster_n2v(tag))
            
            if get_cluster_fuzzy(tag) != target_fuzzy_cluster:
                count_alarms_fuzzy += 1
            if get_cluster_n2v(tag) != target_n2v_cluster:
                count_alarms_n2v += 1
        ### Logica Llamadas
        if policy["severity"] not in selected_severities:
            continue
         
        if trigger_alarm:
            await trigger_action(severity, message, data_register, tag)

async def polling(client):
    try:
        while True:
            hr = await client.read_holding_registers(address=0, count=10, device_id=1)
            ir = await client.read_input_registers(address=0,count=10,device_id=1)
            co = await client.read_coils(address=0,count=10,device_id=1)
            
            await apply_plan_policy(hr, [], co, ir)
            if time.time() - minutes >= 3600 :
                # escribir cantidad de minutos en un archivo
                if not result_dict["60"]:
                    result_dict["60"] = count_alarms
                    result_dict_fuzzy["60"] = count_alarms_fuzzy
                    result_dict_n2v["60"] = count_alarms_n2v
                    with open("resultados_middleware.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                    with open("resultados_middleware_fuzzy.json", "w") as f:
                        json.dump(result_dict_fuzzy, f, indent=4)
                    with open("resultados_middleware_n2v.json", "w") as f:
                        json.dump(result_dict_n2v, f, indent=4)
            elif time.time() - minutes >= 3000 :
               if not result_dict["50"]:
                    result_dict["50"] = count_alarms
                    result_dict_fuzzy["50"] = count_alarms_fuzzy
                    result_dict_n2v["50"] = count_alarms_n2v
                    with open("resultados_middleware.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                    with open("resultados_middleware_fuzzy.json", "w") as f:
                        json.dump(result_dict_fuzzy, f, indent=4)
                    with open("resultados_middleware_n2v.json", "w") as f:
                        json.dump(result_dict_n2v, f, indent=4)
            elif time.time() - minutes >= 2400 :
                if not result_dict["40"]:
                    result_dict["40"] = count_alarms
                    result_dict_fuzzy["40"] = count_alarms_fuzzy
                    result_dict_n2v["40"] = count_alarms_n2v
                    with open("resultados_middleware.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                    with open("resultados_middleware_fuzzy.json", "w") as f:
                        json.dump(result_dict_fuzzy, f, indent=4)
                    with open("resultados_middleware_n2v.json", "w") as f:
                        json.dump(result_dict_n2v, f, indent=4)
            elif time.time() - minutes >= 1800 :
                if not result_dict["30"]:
                    result_dict["30"] = count_alarms
                    result_dict_fuzzy["30"] = count_alarms_fuzzy
                    result_dict_n2v["30"] = count_alarms_n2v
                    with open("resultados_middleware.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                    with open("resultados_middleware_fuzzy.json", "w") as f:
                        json.dump(result_dict_fuzzy, f, indent=4)
                    with open("resultados_middleware_n2v.json", "w") as f:
                        json.dump(result_dict_n2v, f, indent=4)
            elif time.time() - minutes >= 1200 :
                if not result_dict["20"]:
                    result_dict["20"] = count_alarms
                    result_dict_fuzzy["20"] = count_alarms_fuzzy
                    result_dict_n2v["20"] = count_alarms_n2v
                    with open("resultados_middleware.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                    with open("resultados_middleware_fuzzy.json", "w") as f:
                        json.dump(result_dict_fuzzy, f, indent=4)
                    with open("resultados_middleware_n2v.json", "w") as f:
                        json.dump(result_dict_n2v, f, indent=4)
            elif time.time() - minutes >= 600 :
                if not result_dict["10"]:
                    result_dict["10"] = count_alarms
                    result_dict_fuzzy["10"] = count_alarms_fuzzy
                    result_dict_n2v["10"] = count_alarms_n2v
                    with open("resultados_middleware.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                    with open("resultados_middleware_fuzzy.json", "w") as f:
                        json.dump(result_dict_fuzzy, f, indent=4)
                    with open("resultados_middleware_n2v.json", "w") as f:
                        json.dump(result_dict_n2v, f, indent=4)
    
    except Exception as e:
        print(f"Error en polling: {e}")

async def main():
    
    client = AsyncModbusTcpClient("127.0.0.1", port=5020)
    
    try:
        await manager.connect()
        print(" Conectado al AMI")

        await client.connect()
        if not client.connected:
            raise Exception(" Fallo al conectar con el PLC simulado")

        await polling(client)

    finally:
        client.close()
        manager.close()

if __name__ == "__main__":
    asyncio.run(main())
