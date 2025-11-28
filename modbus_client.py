import asyncio
from pymodbus.client import AsyncModbusTcpClient
import time
intervalo = 5 # Intervalo llenado
import json
intervalo_push = 1# Intervalo Push 
import random

async def clean_states(client):
    await client.write_register(0, 0, device_id=1) # Limpia Nivel
    await client.write_register(1, 0, device_id=1)
    await client.write_register(2, 0, device_id=1) 
    await client.write_register(3, 0, device_id=1)
    await client.write_register(4, 0, device_id=1)
    await client.write_register(5, 0, device_id=1)
    await client.write_register(6, 0, device_id=1)
    await client.write_register(7, 0, device_id=1)

    # Emiter
    await client.write_coil(1,False,device_id=1)               
    await client.write_coil(0,False,device_id=1)

    # Brazos
    await client.write_coil(4,False,device_id=1)
    await client.write_coil(5,False,device_id=1)
    await client.write_coil(9,False,device_id=1)
    # Pushers
    await client.write_coil(6,False,device_id=1)
    await client.write_coil(7, False, device_id=1)
async def main():
    client = AsyncModbusTcpClient("192.168.30.10", port=5020)
    await client.connect()
    await clean_states(client)
    if not client.connected:
        return
    # Estados Falla Señal

    falla_señal_tanque_1 = False

    #Estados Iniciales
    llenado_botella1 = False
    llenado_botella2 = False
    tiempo_llenado1 = None
    tiempo_llenado2 = None

    tiempo_push = None
    push_action = False

    PROCESS_STARTED = False

    count_pusher = 0  

    vision_blue = False
    vision_green = False
    tiempo_push_blue = None
    tiempo_push_green = None
    push_action_blue = False
    push_action_green = False
    count_pusher_blue = 0
    count_pusher_green = 0

    await client.write_coil(2,True,device_id=1)
    await client.write_coil(3,True,device_id=1)                            
    # Resultados
    minutes = time.time()
    count_alarms = 0
    alarm_states = {"valvula_TO_salida":False,"valvula_TO":False,"señal_T1": False,"valvula_T1_salida":False, "valvula_T1_llenado": False, "linea_1": False, "nivel_T0_bajo": False,"nivel_T0_bajo_bajo": False, "nivel_T1_bajo": False,"nivel_T1_bajo_bajo": False,"vibracion":True}
    result_dict = {"10":None,"20":None,"30": None,"40": None,"50":None,"60":None}
    try:
        
        while True:
            
            discrete_register = await client.read_discrete_inputs(address=0,count=11,device_id=1)
            input_register = await client.read_input_registers(address=0,count=8,device_id=1)
            holding_register = await client.read_holding_registers(address=0,count=5,device_id=1)
            ########################### LOGICA TANQUES
            # Tanque 0 Principal
            if(discrete_register.bits[0]):
                await client.write_register(0, 1000, device_id=1)
            if(not discrete_register.bits[1]):
                await client.write_register(0, 0, device_id=1)
               
            if( not PROCESS_STARTED and input_register.registers[0]>= 250):
                await client.write_register(1, 1000, device_id=1) # Descarga
                # Tanque 1 y 2 se llenan
                await client.write_register(2, 1000, device_id=1)
                await client.write_register(3, 1000, device_id=1)
            # Nivel Tanque 0
            if  PROCESS_STARTED and input_register.registers[0] <= 250: 
                if not alarm_states["nivel_T0_bajo"]:
                    count_alarms += 1
                if not alarm_states["vibracion"]:
                    
                    if random.random() < 0.3:
                        await client.write_register(6, 1000, device_id=1)
                        count_alarms += 1
                        alarm_states["vibracion"] = True
                    
                alarm_states["nivel_T0_bajo"] = True
            if  PROCESS_STARTED and input_register.registers[0] > 250:

                alarm_states["nivel_T0_bajo"] = False
                await client.write_register(6, 0, device_id=1)
                alarm_states["vibracion"] = False
            # Logica de seguridad
            
            
            if  PROCESS_STARTED and input_register.registers[0] <= 150:  
                if not alarm_states["nivel_T0_bajo_bajo"]:
                    count_alarms += 1
                    
                alarm_states["nivel_T0_bajo_bajo"] = True
                await client.write_register(1, 0, device_id=1) # Cerrar Descarga
                if not alarm_states["valvula_TO_salida"]:
                    count_alarms += 1
                    
                alarm_states["valvula_TO_salida"] = True
               
                if not alarm_states["valvula_T1_llenado"]:
                    count_alarms += 1
                   
                alarm_states["valvula_T1_llenado"] = True
                await client.write_register(2, 0, device_id=1)# Cerrar Valvulas de llenado
                if not alarm_states["valvula_T1_salida"]:
                    count_alarms += 1
                alarm_states["valvula_T1_salida"] = True
                await client.write_register(3, 0, device_id=1)# Cerrar Valvula de llenado
            if  PROCESS_STARTED and input_register.registers[0] > 150 and alarm_states["nivel_T0_bajo_bajo"]:  
                   apertura_t0 = holding_register.registers[0]
                   apertura_t1 = holding_register.registers[2]
                   alarm_states["nivel_T0_bajo_bajo"] = False
                   alarm_states["valvula_T1_llenado"] = False
                   alarm_states["valvula_TO_salida"] = False
                   alarm_states["valvula_T1_salida"] = False
                   await client.write_register(0, apertura_t0, device_id=1)
                   await client.write_register(1, 1000, device_id=1)
                   await client.write_register(3, 1000, device_id=1) 
                   await client.write_register(2, apertura_t1, device_id=1) 
            # Falla Valvula suministro tanque 0
            
            if PROCESS_STARTED and holding_register.registers[0] == 0:
                if not alarm_states["valvula_TO"]:
                    count_alarms += 1
                alarm_states["valvula_TO"] = True
                # Contar alarma

            
            if PROCESS_STARTED and alarm_states["valvula_TO"] and holding_register.registers[0] == 1000:
                alarm_states["valvula_TO"] = False

            # Mala señal de tanque 1
            if PROCESS_STARTED and input_register.registers[4] == 1000:
                if not alarm_states["señal_T1"]:
                    count_alarms += 1 # Contar alarma
                alarm_states["señal_T1"] = True
                falla_señal_tanque_1 = True
                if not alarm_states["valvula_T1_salida"]:
                    count_alarms += 1 # Contar alarma
                alarm_states["valvula_T1_salida"] = True
                await client.write_register(4, 0, device_id=1) # Cerrado valvula descarga
                if not alarm_states["valvula_T1_llenado"]:
                    count_alarms += 1 # Contar alarma
                alarm_states["valvula_T1_llenado"] = True
                await client.write_register(2, 0, device_id=1) # Cerrado valvula llenado
                if not alarm_states["linea_1"]:
                    count_alarms += 1 # Contar alarma
                alarm_states["linea_1"] = True
                await client.write_coil(9,True,device_id=1) # Fallo de Actuador Brazo

            if PROCESS_STARTED and input_register.registers[4] != 1000 and falla_señal_tanque_1:
                falla_señal_tanque_1 = False
                await client.write_register(4, 1000, device_id=1) # Abre valvula descarga
                await client.write_register(2, 1000, device_id=1) # Abre valvula llenado
                await client.write_coil(9,False,device_id=1) # Apagado Fallo de Actuador Brazo
                alarm_states["linea_1"] = False
                alarm_states["valvula_T1_llenado"] = False
                alarm_states["señal_T1"] = False
                alarm_states["valvula_T1_salida"] = False



            # Nivel Tanque 1
            if  PROCESS_STARTED and input_register.registers[1] <= 250: 
                if not alarm_states["nivel_T1_bajo"]:
                    count_alarms += 1
                
                alarm_states["nivel_T1_bajo"] = True
            if  PROCESS_STARTED and input_register.registers[1] > 250:
                alarm_states["nivel_T1_bajo"] = False
            # Logica de seguridad
            
            
            if  PROCESS_STARTED and input_register.registers[1] <= 150:  
                if not alarm_states["nivel_T1_bajo_bajo"]:
                    count_alarms += 1
                    
                alarm_states["nivel_T1_bajo_bajo"] = True
                await client.write_register(4, 0, device_id=1) # Cerrar Descarga
                if not alarm_states["valvula_T1_salida"]:
                    count_alarms += 1
                    
                alarm_states["valvula_T1_salida"] = True
               
                
            if  PROCESS_STARTED and input_register.registers[1] > 150 and alarm_states["nivel_T1_bajo_bajo"]:  
                   alarm_states["nivel_T1_bajo_bajo"] = False
                   alarm_states["valvula_T1_salida"] = False
                   await client.write_register(4, 1000, device_id=1)



            
            # Tanque 1 
            if( input_register.registers[1]>= 250 and not PROCESS_STARTED):
                await client.write_register(4, 1000, device_id=1)
                await client.write_coil(0,True,device_id=1)
            # Tanque 2
            if( input_register.registers[2]>= 250 and not PROCESS_STARTED):
                 await client.write_register(5, 1000, device_id=1)
                 await client.write_coil(1,True,device_id=1)   
                 PROCESS_STARTED = True

            ############################################ 


            ######################################### LOGICA EMITTERS


            # Emitter 1
            if(PROCESS_STARTED and discrete_register.bits[3] and not tiempo_llenado1 and not discrete_register.bits[4]):
                await client.write_coil(1,False,device_id=1) # Emiter
                await client.write_coil(3,False,device_id=1) # Faja
                await client.write_coil(4,True,device_id=1)  #Brazo
                llenado_botella1 = True     
                tiempo_llenado1 = time.time()    
            # Emitter 2
            if(PROCESS_STARTED and discrete_register.bits[2] and not tiempo_llenado2 and not discrete_register.bits[5]):
                await client.write_coil(0,False,device_id=1)
                await client.write_coil(2,False,device_id=1)   
                await client.write_coil(5,True,device_id=1)   #Brazo
                llenado_botella2 = True    
                tiempo_llenado2 = time.time()         

            ######################################### LOGICA LLENADO BOTELLAS
            if llenado_botella1 and time.time() - tiempo_llenado1 >= intervalo and holding_register.registers[4] !=0 :
                await client.write_coil(3,True,device_id=1) # Faja
                llenado_botella1 = False
                await client.write_coil(4,False,device_id=1) # Brazo

            if llenado_botella2 and time.time() - tiempo_llenado2 >= intervalo :
                await client.write_coil(2,True,device_id=1)# Faja
                llenado_botella2 = False
                
                
                await client.write_coil(5,False,device_id=1)

            if  tiempo_llenado1 and discrete_register.bits[4]: 
               
                await client.write_coil(1,True,device_id=1) # Emiter
                tiempo_llenado1 = None

            if tiempo_llenado2 and discrete_register.bits[5]: 
               
                await client.write_coil(0,True,device_id=1) # Emiter
                tiempo_llenado2 = None
            
           
            ############################################### LOGICA PUSHER
            
            if discrete_register.bits[6]:  
                if not push_action:  
                    count_pusher += 1  
                    
                    if count_pusher % 200 == 0:
                        tiempo_push = time.time()
                        push_action = True
                        await client.write_coil(6, True, device_id=1)
                       
            # Desactivar pusher después de intervalo
            if push_action and tiempo_push and time.time() - tiempo_push >= intervalo_push:
                await client.write_coil(6, False, device_id=1)
                push_action = False
                tiempo_push = None
        
            ################################################  LOGICA CATEGORIZAR
            ## Categoria Azul
            if discrete_register.bits[7] :
               
                vision_blue = True
            if vision_blue and discrete_register.bits[9]:
                
                count_pusher_blue += 1
                if count_pusher_blue % 60 ==0:
                        await client.write_coil(7, True, device_id=1)
                        tiempo_push_blue = time.time()
                        push_action_blue = True
            if push_action_blue and tiempo_push_blue and time.time() - tiempo_push_blue >= 0.8:
                await client.write_coil(7, False, device_id=1)
                push_action_blue = False
                tiempo_push_blue = None
                vision_blue = False
            ## Categoria Verder        
            if discrete_register.bits[8] :
               
                vision_green = True
            if vision_green and discrete_register.bits[10]:
                
                count_pusher_green += 1
                if count_pusher_green % 50 ==0:
                        await client.write_coil(8, True, device_id=1)
                        tiempo_push_green = time.time()
                        push_action_green = True
            if push_action_green and tiempo_push_green and time.time() - tiempo_push_green >= 0.8:
                await client.write_coil(8, False, device_id=1)
                push_action_green = False
                tiempo_push_green = None
                vision_green = False
            
            ######################################## TEMPERATURA
            await client.write_register(7, 0, device_id=1)
            if random.random() < 0.0001:
                print("Ebtre aca")
                count_alarms +=1
                await client.write_register(7, 550, device_id=1)

            ################################################ RESULTADOS

            if time.time() - minutes >= 3600 :
                # escribir cantidad de minutos en un archivo
                if not result_dict["60"]:
                    result_dict["60"] = count_alarms
                    with open("resultados_total.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
                
            elif time.time() - minutes >= 3000 :
               if not result_dict["50"]:
                    result_dict["50"] = count_alarms
                    with open("resultados_total.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
            elif time.time() - minutes >= 2400 :
                if not result_dict["40"]:
                    result_dict["40"] = count_alarms
                    with open("resultados_total.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
            elif time.time() - minutes >= 1800 :
                if not result_dict["30"]:
                    result_dict["30"] = count_alarms
                    with open("resultados_total.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
            elif time.time() - minutes >= 1200 :
                if not result_dict["20"]:
                    result_dict["20"] = count_alarms
                    with open("resultados_total.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
            elif time.time() - minutes >= 600 :
                if not result_dict["10"]:
                    result_dict["10"] = count_alarms
                    with open("resultados_total.json", "w") as f:
                        json.dump(result_dict, f, indent=4)
            
            
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())