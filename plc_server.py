import asyncio
import random
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock

# Crear memoria inicial del PLC simulado
store = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(0, [0]*100),  # Discrete Inputs
    co=ModbusSequentialDataBlock(0, [0]*100),  # Coils
    hr=ModbusSequentialDataBlock(0, [0]*100),  # Holding Registers
    ir=ModbusSequentialDataBlock(0, [0]*100),  # Input Registers
)
context = ModbusServerContext(devices=store, single=True)

async def update_registers():
    """Simula el PLC funcionamiento escribiendo iterativamente los registros"""
    while True:
        # Alarmas binarias en HR
        store.setValues(3, 0, [random.choice([0, 1])])  # HR40001 - Presión alta
        store.setValues(3, 1, [random.choice([0, 1])])  # HR40002 - Temp alta
        store.setValues(3, 2, [random.choice([0, 1])])  # HR40003 - Falla motor
        store.setValues(3, 3, [random.choice([0, 1, 2])])  # HR40004 - Estado

        # Analógico en HR
        store.setValues(3, 4, [random.randint(50, 150)])  # HR40005

        # Simular entradas digitales (DI)
        store.setValues(2, 0, [random.choice([0, 1])])  # DI10001 - Sensor puerta

        # Simular coils (salidas)
        store.setValues(1, 0, [random.choice([0, 1])])  # CO00001 - Luz encendida

        # Simular input registers (sensores analógicos)
        store.setValues(4, 0, [random.randint(200, 800)])  # IR30001 - Caudal

        print(" Actualización de registros Modbus")
        await asyncio.sleep(5)  # cada 5 segundos

async def main():
    # Inicia el servidor y el ciclo de simulación en paralelo
    await asyncio.gather(
        StartAsyncTcpServer(context, address=("0.0.0.0", 5020)),  # puerto 5020
        update_registers()
    )

if __name__ == "__main__":
    asyncio.run(main())
