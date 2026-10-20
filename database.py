import sqlite3
from datetime import datetime

DB_NAME = "parqueadero.db"

# Tarifas sugeridas por minuto (en COP)
TARIFAS_POR_DEFECTO = {
    "Carro": 120,
    "Moto": 60,
    "Bicicleta": 20,
    "Bicicleta Eléctrica": 35,
    "Scooter Eléctrico": 30
}

def init_db():
    """Inicializa la base de datos con los 95 espacios categorizados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de espacios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS espacios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_espacio TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL,
            estado TEXT NOT NULL, -- 'Disponible' o 'Ocupado'
            placa TEXT,
            tipo_vehiculo TEXT,
            hora_entrada TEXT
        )
    ''')
    
    # Tabla de historial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_espacio TEXT,
            tipo_vehiculo TEXT,
            placa TEXT,
            hora_entrada TEXT,
            hora_salida TEXT,
            total_pagado REAL
        )
    ''')
    
    conn.commit()
    
    # Generar espacios de forma dinámica si la base de datos está vacía
    cursor.execute("SELECT COUNT(*) FROM espacios")
    if cursor.fetchone()[0] == 0:
        espacios_iniciales = []
        
        # 1. 30 Carros (C-01 a C-30)
        for i in range(1, 31):
            espacios_iniciales.append((f"C-{i:02d}", "Carro", "Disponible"))
            
        # 2. 30 Motos (M-01 a M-30)
        for i in range(1, 31):
            espacios_iniciales.append((f"M-{i:02d}", "Moto", "Disponible"))
            
        # 3. 20 Bicicletas (B-01 a B-20)
        for i in range(1, 21):
            espacios_iniciales.append((f"B-{i:02d}", "Bicicleta", "Disponible"))
            
        # 4. 10 Bicicletas Eléctricas (BE-01 a BE-10)
        for i in range(1, 11):
            espacios_iniciales.append((f"BE-{i:02d}", "Bicicleta Eléctrica", "Disponible"))
            
        # 5. 5 Scooters Eléctricos (SE-01 a SE-05)
        for i in range(1, 6):
            espacios_iniciales.append((f"SE-{i:02d}", "Scooter Eléctrico", "Disponible"))
            
        cursor.executemany("INSERT INTO espacios (numero_espacio, tipo, estado) VALUES (?, ?, ?)", espacios_iniciales)
        conn.commit()
        
    conn.close()

def obtener_espacios():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero_espacio, tipo, estado, placa, tipo_vehiculo, hora_entrada FROM espacios")
    datos = cursor.fetchall()
    conn.close()
    return datos

def registrar_entrada(numero_espacio, placa, tipo_vehiculo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE espacios 
        SET estado = 'Ocupado', placa = ?, tipo_vehiculo = ?, hora_entrada = ? 
        WHERE numero_espacio = ? AND estado = 'Disponible'
    ''', (placa.upper(), tipo_vehiculo, hora_actual, numero_espacio))
    conn.commit()
    cambios = cursor.rowcount
    conn.close()
    return cambios > 0

def registrar_salida(numero_espacio, tarifa_por_minuto):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT placa, tipo_vehiculo, hora_entrada FROM espacios WHERE numero_espacio = ? AND estado = 'Ocupado'", (numero_espacio,))
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        return None, None, 0, 0
        
    placa, tipo_vehiculo, hora_entrada_str = resultado
    hora_salida = datetime.now()
    hora_entrada = datetime.strptime(hora_entrada_str, "%Y-%m-%d %H:%M:%S")
    
    diferencia = hora_salida - hora_entrada
    minutos = int(diferencia.total_seconds() / 60)
    if minutos < 1:
        minutos = 1
        
    total_pagar = minutos * tarifa_por_minuto
    hora_salida_str = hora_salida.strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO historial (numero_espacio, tipo_vehiculo, placa, hora_entrada, hora_salida, total_pagado)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (numero_espacio, tipo_vehiculo, placa, hora_entrada_str, hora_salida_str, total_pagar))
    
    cursor.execute('''
        UPDATE espacios 
        SET estado = 'Disponible', placa = NULL, tipo_vehiculo = NULL, hora_entrada = NULL 
        WHERE numero_espacio = ?
    ''', (numero_espacio,))
    
    conn.commit()
    conn.close()
    
    return placa, tipo_vehiculo, minutos, total_pagar

def obtener_historial():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero_espacio, tipo_vehiculo, placa, hora_entrada, hora_salida, total_pagado FROM historial ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos