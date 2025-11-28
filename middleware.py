import asyncio
from panoramisk.manager import Manager
from operator import itemgetter
from pymodbus.client import AsyncModbusTcpClient
import json
import time
# AMI (puede quedarse global porque panoramisk crea su loop internamente)
manager = Manager(
    host='192.168.40.10',  # Asterisk AMI
    port=5038,
    username='amiuser',
    secret='luis'
)

# Asterisk Actions
actions = {
    "action_playback": {
        "Action": "Originate",
        "Channel": "PJSIP/1001",
        "Context": "interno",
        "Exten": "1001",
        "Priority": "1",
        "CallerID": "Middleware <1000>",
        "Timeout": "30000",
        "Async": "true",
        "Application": "Playback",
        "Data": "es/vm-instructions"
    },
    "action_message" : {
        "Action": "MessageSend",
        "To": "PJSIP/mantenimiento_electrico",  
        "From": "<Middleware>",       
        "Body": None
    }
}

# Alarm states
alarm_states = {}
async def trigger_action(severity, message, data, tag,exten):
    print(exten)
    print(f" Alarma disparada: {tag} [{severity}] {message} | valor={data} extention ={exten}")
    extention = exten if exten else 1001
    if extention == 1002 :
        actions["action_playback"]["Exten"] = str(extention)
        actions["action_playback"]["Channel"] = "PJSIP/1002"
    else:
        actions["action_playback"]["Exten"] = str(extention)
        actions["action_playback"]["Channel"] = "PJSIP/1001"
    print(actions["action_playback"]["Exten"])
    response = await manager.send_action(actions["action_playback"])
    print(" Originate response:", response)
  

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
        
        if policy["severity"] not in selected_severities:
            continue
        
        policy_type = policy["source"]["type"]
        register = registers_dictionary.get(policy_type, [])
        if not register:
            continue

        data_register = register[policy["source"]["address"]]
        tag, severity, message,exten = itemgetter("tag", "severity", "message","exten")(policy)
        
        trigger_alarm = check_and_update_alarm(policy, data_register)
        if trigger_alarm:
            await trigger_action(severity, message, data_register, tag,exten)

async def polling(client):
    try:
        while True:
            hr = await client.read_holding_registers(address=0, count=7, device_id=1)
            ir = await client.read_input_registers(address=0,count=10,device_id=1)
            co = await client.read_coils(address=0,count=10,device_id=1)

            await apply_plan_policy(hr, [], co, ir)

    except Exception as e:
        print(f"Error en polling: {e}")

async def main():
    
    client = AsyncModbusTcpClient("192.168.30.10", port=5020)
    
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
