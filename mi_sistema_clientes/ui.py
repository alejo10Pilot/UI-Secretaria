import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dateutil.relativedelta import relativedelta
from db import (
    obtener_datos_cliente,
    obtener_nombre_cliente,
    calcular_interes,
    registrar_interes,
    registrar_abono,
    obtener_todos_los_clientes,
    obtener_ultimo_pago_hasta_por_interes
)

def crear_vista_general():
    def abrir_sistema_registro():
        raiz.destroy()
        crear_ventana()

    def cargar_clientes(tabla):
        for fila in tabla.get_children():
            tabla.delete(fila)
        clientes = obtener_todos_los_clientes()
        for cliente in clientes:
            tabla.insert('', 'end', values=(
                cliente[0],
                cliente[1],
                f"${cliente[2]:,.2f}",
                cliente[3],
                cliente[4],
            ))

    raiz = tk.Tk()
    raiz.title("Vista General de Clientes")
    raiz.geometry("1000x500")

    columnas = ("ID", "Nombre", "Saldo", "Último Pago", "Pago Hasta")
    tabla = ttk.Treeview(raiz, columns=columnas, show="headings")
    for col in columnas:
        tabla.heading(col, text=col)
        tabla.column(col, anchor="center")
    tabla.pack(expand=True, fill="both", padx=10, pady=10)

    cargar_clientes(tabla)

    btn_modificar = tk.Button(raiz, text="Modificar", command=abrir_sistema_registro)
    btn_modificar.pack(pady=10)

    raiz.mainloop()

def crear_ventana():
    raiz = tk.Tk()
    raiz.title("Sistema de Registro")
    raiz.geometry("400x300")

    def abrir_registro(tipo_registro):
        ventana = tk.Toplevel()
        ventana.title(f"Registrar {tipo_registro.capitalize()}")
        ventana.geometry("400x500")

        labels = {
            "numero_recibo": "Número de Recibo",
            "id_cliente": "ID Cliente",
            "fecha_pago": "Fecha Pago (YYYY-MM-DD)",
            "observaciones": "Observaciones"
        }

        entradas = {}
        for key, texto in labels.items():
            tk.Label(ventana, text=texto).pack()
            entrada = tk.Entry(ventana)
            if key == "fecha_pago":
                entrada.insert(0, datetime.today().strftime('%Y-%m-%d'))
            entrada.pack()
            entradas[key] = entrada

        if tipo_registro == "interes":
            tk.Label(ventana, text="Seleccione el porcentaje de interés").pack()
            porcentaje_var = tk.StringVar()
            porcentaje_combo = ttk.Combobox(ventana, textvariable=porcentaje_var)
            porcentaje_combo['values'] = ["1.8%", "2%", "2.2%"]
            porcentaje_combo.pack()
            tk.Label(ventana, text="¿Cuántos meses paga?").pack()
            meses_var = tk.IntVar(value=1)
            tk.Spinbox(ventana, from_=1, to=12, textvariable=meses_var, width=5).pack()

        if tipo_registro == "abono":
            tk.Label(ventana, text="Abono a capital").pack()
            abono_var = tk.Entry(ventana)
            abono_var.insert(0, "0")
            abono_var.pack()

        def confirmar():
            try:
                id_cliente = int(entradas["id_cliente"].get())
                saldo_actual, _ = obtener_datos_cliente(id_cliente)

                if tipo_registro == "interes":
                    pago_hasta_actual = obtener_ultimo_pago_hasta_por_interes(id_cliente)
                    if not pago_hasta_actual:
                        pago_hasta_actual = datetime.strptime(entradas["fecha_pago"].get(), "%Y-%m-%d")

                    porcentaje = float(porcentaje_var.get().replace('%', '')) / 100
                    meses = meses_var.get()
                    monto = calcular_interes(saldo_actual, porcentaje) * meses
                    nuevo_pago_hasta = pago_hasta_actual + relativedelta(months=meses)


                    resumen = f"""
NOMBRE CLIENTE: {obtener_nombre_cliente(id_cliente)}
Nº RECIBO: {entradas['numero_recibo'].get()}
FECHA PAGO: {entradas['fecha_pago'].get()}
MESES PAGADOS: {meses}
PAGO HASTA: {nuevo_pago_hasta}
MONTO: ${monto:,.2f}
SALDO: ${saldo_actual:,.2f}
TIPO: interés
OBSERVACIONES: {entradas['observaciones'].get()}
CONSIGNÓ A: {consigno_var.get()}
"""
                    if messagebox.askokcancel("Confirmar Registro", resumen):
                        registrar_interes({
                            "numero_recibo": entradas["numero_recibo"].get(),
                            "id_cliente": id_cliente,
                            "fecha_pago": entradas["fecha_pago"].get(),
                            "pago_hasta": nuevo_pago_hasta,
                            "abono_intereses": monto,
                            "saldo_restante": saldo_actual,
                            "observaciones": entradas["observaciones"].get(),
                            "consigno_a": consigno_var.get()
                        })
                        ventana.destroy()

                elif tipo_registro == "abono":
                    abono = float(abono_var.get())
                    nuevo_saldo = saldo_actual - abono
                    resumen = f"""
NOMBRE CLIENTE: {obtener_nombre_cliente(id_cliente)}
Nº RECIBO: {entradas['numero_recibo'].get()}
FECHA PAGO: {entradas['fecha_pago'].get()}
ABONO CAPITAL: ${abono:,.2f}
NUEVO SALDO: ${nuevo_saldo:,.2f}
TIPO: abono
OBSERVACIONES: {entradas['observaciones'].get()}
CONSIGNÓ A: {consigno_var.get()}
"""
                    if messagebox.askokcancel("Confirmar Abono", resumen):
                        registrar_abono({
                            "numero_recibo": entradas["numero_recibo"].get(),
                            "id_cliente": id_cliente,
                            "fecha_pago": entradas["fecha_pago"].get(),
                            "abono_capital": abono,
                            "saldo_restante": nuevo_saldo,
                            "observaciones": entradas["observaciones"].get(),
                            "consigno_a": consigno_var.get()
                        })
                        ventana.destroy()

            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Label(ventana, text="Consignó a:").pack()
        consigno_var = tk.StringVar()
        consigno_combo = ttk.Combobox(ventana, textvariable=consigno_var)
        consigno_combo['values'] = ["Efectivo", "Alejo", "Angela", "Andrea", "Carlos", "Maria"]
        consigno_combo.pack()

        tk.Button(ventana, text="Confirmar", command=confirmar).pack(pady=10)

    def mostrar_clientes():
        raiz.destroy()
        crear_vista_general()

    tk.Button(raiz, text="Registrar Interés", width=30, command=lambda: abrir_registro("interes")).pack(pady=10)
    tk.Button(raiz, text="Registrar Abono", width=30, command=lambda: abrir_registro("abono")).pack(pady=10)
    tk.Button(raiz, text="Ver Clientes", width=30, command=mostrar_clientes).pack(pady=10)

    raiz.mainloop()
