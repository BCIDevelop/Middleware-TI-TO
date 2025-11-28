import asyncio
from panoramisk.manager import Manager

async def main():
    manager = Manager(
        loop=asyncio.get_event_loop(),
        host='192.168.0.16',   # Asterisk AMI
        port=5038,          # puerto AMI 
        username='amiuser',  
        secret='luis'  
    )

    try:
        await manager.connect()         
        print("✅ Conectado al AMI")

        # ORIGINATE: genera una llamada
        actions = {
            "action":{
                 "Action": "Originate",
                 "Channel": "PJSIP/mantenimiento",    # canal a marcar
                 "Context": "internal",        # contexto en extensions.conf
                 "Exten": "1002",                     # extensión destino
                 "Priority": "1",                     # prioridad dentro del contexto
                 "CallerID": "Middleware <1000>",     
                 "Timeout": "30000",                   # tiempo máximo en ms (30s)
                 "Async": "true"
            },
            "action_playback":{
                 "Action": "Originate",
                 "Channel": "PJSIP/mantenimiento",    # canal a marcar
                 "Context": "internal",        # contexto en extensions.conf
                 "Priority": "1",                   # prioridad dentro del contexto
                 "Exten": "1002", 
                 "CallerID": "Middleware <1000>",    
                 "Timeout": "30000",                   # tiempo máximo en ms (30s)
                 "Async": "true",
                 "Application": "Playback",
                 "Data": "es/custom/alarma-8k"
            }

           
        }

        response = await manager.send_action(actions["action_playback"])
        print(" Originate Response:", response)
        # Mantener conexión un rato para ver eventos
        await asyncio.sleep(5)

        # Cerrar conexión
        manager.close()
    except Exception as e:
        print(" Error durante la conexión/acción:", repr(e))
    finally:
        manager.close()           # cierra la conexión
        print(" Conexión cerrada")

if __name__ == '__main__':
    asyncio.run(main())