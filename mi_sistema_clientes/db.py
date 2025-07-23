import mysql.connector
from mysql.connector import Error
from dateutil.relativedelta import relativedelta
from datetime import datetime

def conectar():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Zuluaga403",
        database="Hipotecas",
        port="3306"
    )

def calcular_interes(saldo_restante, porcentaje):
    return round(saldo_restante * porcentaje, 2)

def obtener_datos_cliente(id_cliente):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT saldo_restante, pago_hasta FROM clientes WHERE id_cliente = %s",
        (id_cliente,)
    )
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return resultado
    else:
        raise ValueError("Cliente no encontrado")

def obtener_nombre_cliente(id_cliente):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nombre_cliente FROM clientes WHERE id_cliente = %s",
        (id_cliente,)
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else "No encontrado"

def registrar_interes(datos):
    # datos debe contener: numero_recibo, id_cliente, fecha_pago (str),
    # pago_hasta (date), abono_intereses (float), saldo_restante, observaciones, consigno_a, tipo='interes'
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recibos (
            numero_recibo, id_cliente, fecha_pago,
            pago_hasta, abono_intereses, saldo_restante,
            tipo, observaciones, consigno_a
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        datos["numero_recibo"],
        datos["id_cliente"],
        datos["fecha_pago"],
        datos["pago_hasta"],
        datos["abono_intereses"],
        datos["saldo_restante"],
        "interes",
        datos["observaciones"],
        datos["consigno_a"]
    ))
    cursor.execute("""
        UPDATE clientes
           SET fecha_ultimo_pago = %s,
               pago_hasta = %s
         WHERE id_cliente = %s
    """, (
        datos["fecha_pago"],
        datos["pago_hasta"],
        datos["id_cliente"]
    ))
    conn.commit()
    conn.close()

def registrar_abono(datos):
    # datos debe contener: numero_recibo, id_cliente, fecha_pago, abono_capital, saldo_restante, observaciones, consigno_a
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recibos (
            numero_recibo, id_cliente, fecha_pago,
            abono_capital, saldo_restante, tipo,
            observaciones, consigno_a
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        datos["numero_recibo"],
        datos["id_cliente"],
        datos["fecha_pago"],
        datos["abono_capital"],
        datos["saldo_restante"],
        "abono",
        datos["observaciones"],
        datos["consigno_a"]
    ))
    cursor.execute("""
        UPDATE clientes
           SET saldo_restante = %s
         WHERE id_cliente = %s
    """, (
        datos["saldo_restante"],
        datos["id_cliente"]
    ))
    conn.commit()
    conn.close()

def registrar_abono_parcial(datos):
    # datos debe contener: numero_recibo, id_cliente, fecha_pago, abono_parcial, saldo_restante, observaciones, consigno_a
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO recibos (
        numero_recibo, id_cliente, fecha_pago,
        abono_capital, saldo_restante, tipo,
        observaciones, consigno_a
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (
    datos["numero_recibo"],
    datos["id_cliente"],
    datos["fecha_pago"],
    datos["abono_parcial"],
    datos["saldo_restante"],
    "abono_parcial",  # <-- aquí estaba "interes_parcial"
    datos["observaciones"],
    datos["consigno_a"]
))
    # NO tocamos pago_hasta ni fecha_ultimo_pago
    conn.commit()
    conn.close()

def obtener_todos_los_clientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_cliente, nombre_cliente, saldo_restante, fecha_ultimo_pago, pago_hasta
          FROM clientes
    """)
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_ultimo_pago_hasta_por_interes(id_cliente):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pago_hasta
          FROM recibos
         WHERE id_cliente = %s AND tipo = 'interes'
           AND pago_hasta IS NOT NULL
         ORDER BY fecha_pago DESC
         LIMIT 1
    """, (id_cliente,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado and resultado[0]:
        return datetime.combine(resultado[0], datetime.min.time())
    else:
        raise ValueError("El cliente no tiene registros de interés aún.")
