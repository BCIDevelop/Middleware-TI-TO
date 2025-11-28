import asyncio
from pymodbus.client import AsyncModbusTcpClient
import time

import random


async def main():
    client = AsyncModbusTcpClient("127.0.0.1", port=5020)
    await client.connect()
    
    if not client.connected:
        return

    try:
        
        while True:
            sleep_time = random.randint(20, 60)
            print(f"Durmiendo por {sleep_time}")
            await asyncio.sleep(sleep_time)  # cada 20-60 seg
            # Elegir una válvula aleatoria (ej: tanque 1 o tanque 2)
            valvula = random.choice([0,2])  # registros de válvulas de llenado
            print(f"⚠️ Simulando falla en válvula {valvula}")
            apertura = random.randint(0, 200)
            print(f"Apertura: {apertura}" )
            # Forzar la válvula a cerrarse
            await client.write_register(valvula, 0, device_id=1)

            # Mantenerla fallando entre 3-8 seg
            fail_time = random.randint(3, 8)
            print(f"tiempo de falla {fail_time}")
            await asyncio.sleep(fail_time)

            # Restaurar operación normal
            await client.write_register(valvula, 1000, device_id=1)
            print(f"✅ Válvula {valvula} restaurada")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())