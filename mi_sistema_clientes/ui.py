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
    registrar_abono_parcial,
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
        for c in obtener_todos_los_clientes():
            tabla.insert('', 'end', values=(
                c[0], c[1], f"${c[2]:,.2f}", c[3], c[4]
            ))

    raiz = tk.Tk()
    raiz.title("Vista General de Clientes")
    raiz.geometry("1000x500")

    cols = ("ID", "Nombre", "Saldo", "Último Pago", "Pago Hasta")
    tabla = ttk.Treeview(raiz, columns=cols, show="headings")
    for col in cols:
        tabla.heading(col, text=col)
        tabla.column(col, anchor="center")
    tabla.pack(expand=True, fill="both", padx=10, pady=10)

    cargar_clientes(tabla)
    tk.Button(raiz, text="Modificar", command=abrir_sistema_registro).pack(pady=10)
    raiz.mainloop()

def crear_ventana():
    raiz = tk.Tk()
    raiz.title("Sistema de Registro")
    raiz.geometry("400x300")

    def abrir_registro(tipo):
        ventana = tk.Toplevel(raiz)
        ventana.title(f"Registrar {tipo.capitalize()}")
        ventana.geometry("400x500")

        # campos comunes
        campos = {
            "numero_recibo": "Número de Recibo",
            "id_cliente":    "ID Cliente",
            "fecha_pago":    "Fecha Pago (YYYY-MM-DD)",
            "observaciones": "Observaciones"
        }
        ent = {}
        for k, label in campos.items():
            tk.Label(ventana, text=label).pack()
            e = tk.Entry(ventana)
            if k == "fecha_pago":
                e.insert(0, datetime.today().strftime('%Y-%m-%d'))
            e.pack()
            ent[k] = e

        # extras según tipo
        if tipo == "interes":
            tk.Label(ventana, text="Seleccione % interés").pack()
            pct = tk.StringVar()
            cb = ttk.Combobox(ventana, textvariable=pct, values=["1.8%", "2%", "2.2%"])
            cb.pack()
            tk.Label(ventana, text="¿Meses?").pack()
            meses_var = tk.IntVar(value=1)
            tk.Spinbox(ventana, from_=1, to=12, textvariable=meses_var, width=5).pack()
        elif tipo == "abono":
            tk.Label(ventana, text="Abono a capital").pack()
            abx = tk.Entry(ventana)
            abx.insert(0, "0")
            abx.pack()

        # siempre consignó a
        tk.Label(ventana, text="Consignó a:").pack()
        quien = tk.StringVar()
        cons = ttk.Combobox(ventana, textvariable=quien,
                            values=["Efectivo","Alejo","Maria","Carlos","Andrea","Angela"])
        cons.pack()

        def confirmar():
            cid = int(ent["id_cliente"].get())
            saldo, pago_hasta_cliente = obtener_datos_cliente(cid)

            if tipo == "interes":
                # 1) Fecha de pago ingresada por el usuario
                fecha_str = ent["fecha_pago"].get()
                fecha_usuario = datetime.strptime(fecha_str, "%Y-%m-%d")

                # 2) Definir base: si ya hay pago_hasta en clientes, úsalo; si no, la fecha de usuario
                if pago_hasta_cliente:
                    base = datetime.combine(pago_hasta_cliente, datetime.min.time())
                else:
                    base = fecha_usuario

                # 3) Leer porcentaje y meses, asegurar al menos 1 mes
                porcentaje = float(pct.get().replace('%', '')) / 100
                m = max(1, int(meses_var.get()))

                # 4) Calcular interés y nueva fecha, y **convertir a date**
                monto = calcular_interes(saldo, porcentaje) * m
                nuevo_dt = base + relativedelta(months=m)
                nuevo_fecha = nuevo_dt.date()

                resumen = (
                    f"NOMBRE: {obtener_nombre_cliente(cid)}\n"
                    f"RECIBO: {ent['numero_recibo'].get()}\n"
                    f"FECHA: {fecha_str}\n"
                    f"MES(ES): {m}\n"
                    f"PAGO HASTA: {nuevo_fecha}\n"
                    f"MONTO: ${monto:,.2f}\n"
                    f"SALDO: ${saldo:,.2f}\n"
                    f"TIPO: interés\n"
                    f"OBS: {ent['observaciones'].get()}\n"
                    f"CONSIGNÓ A: {quien.get()}"
                )
                if messagebox.askokcancel("Confirmar", resumen):
                    registrar_interes({
                        "numero_recibo":   ent["numero_recibo"].get(),
                        "id_cliente":      cid,
                        "fecha_pago":      fecha_str,
                        "pago_hasta":      nuevo_fecha,   # <-- date puro
                        "abono_intereses": monto,
                        "saldo_restante":  saldo,
                        "observaciones":   ent["observaciones"].get(),
                        "consigno_a":      quien.get()
                    })
                    ventana.destroy()


            elif tipo == "abono":
                ab = float(abx.get())
                nuevo_saldo = saldo - ab
                resumen = (
                    f"NOMBRE: {obtener_nombre_cliente(cid)}\n"
                    f"RECIBO: {ent['numero_recibo'].get()}\n"
                    f"FECHA: {ent['fecha_pago'].get()}\n"
                    f"ABONO: ${ab:,.2f}\n"
                    f"NUEVO SALDO: ${nuevo_saldo:,.2f}\n"
                    f"TIPO: abono\n"
                    f"OBS: {ent['observaciones'].get()}\n"
                    f"CONSIGNÓ A: {quien.get()}"
                )
                if messagebox.askokcancel("Confirmar", resumen):
                    registrar_abono({
                        "numero_recibo": ent["numero_recibo"].get(),
                        "id_cliente": cid,
                        "fecha_pago": ent["fecha_pago"].get(),
                        "abono_capital": ab,
                        "saldo_restante": nuevo_saldo,
                        "observaciones": ent["observaciones"].get(),
                        "consigno_a": quien.get()
                    })
                    ventana.destroy()


            elif tipo == "abono":
                ab = float(abx.get())
                nuevo_saldo = saldo - ab
                resumen = (
                    f"NOMBRE: {obtener_nombre_cliente(cid)}\n"
                    f"RECIBO: {ent['numero_recibo'].get()}\n"
                    f"FECHA: {ent['fecha_pago'].get()}\n"
                    f"ABONO: ${ab:,.2f}\n"
                    f"NUEVO SALDO: ${nuevo_saldo:,.2f}\n"
                    f"TIPO: abono\n"
                    f"OBS: {ent['observaciones'].get()}\n"
                    f"CONSIGNÓ A: {quien.get()}"
                )
                if messagebox.askokcancel("Confirmar", resumen):
                    registrar_abono({
                        "numero_recibo": ent["numero_recibo"].get(),
                        "id_cliente": cid,
                        "fecha_pago": ent["fecha_pago"].get(),
                        "abono_capital": ab,
                        "saldo_restante": nuevo_saldo,
                        "observaciones": ent["observaciones"].get(),
                        "consigno_a": quien.get()
                    })
                    ventana.destroy()

        tk.Button(ventana, text="Confirmar", command=confirmar).pack(pady=10)




    def abrir_pago_parcial():
        ventana = tk.Toplevel(raiz)
        ventana.title("Registrar Pago Parcial")
        ventana.geometry("500x500")

        # Campos básicos
        campos = {
            "numero_recibo": "Número de Recibo",
            "id_cliente":    "ID Cliente",
            "valor":         "Valor Parcial ($)",
            "observaciones": "Observaciones"
        }
        ent = {}
        for k, lbl in campos.items():
            tk.Label(ventana, text=lbl).pack(pady=(10,0))
            e = tk.Entry(ventana)
            if k == "valor":
                e.insert(0, "0")
            e.pack()
            ent[k] = e

        # Consignó a
        tk.Label(ventana, text="Consignó a:").pack(pady=(10,0))
        quien = tk.StringVar()
        cons = ttk.Combobox(
            ventana, textvariable=quien,
            values=["Efectivo","Alejo","Maria","Carlos","Andrea","Angela"],
            state="readonly"
        )
        cons.pack()

        def confirmar_parcial():
            try:
                rec = ent["numero_recibo"].get()
                cid = int(ent["id_cliente"].get())
                val = float(ent["valor"].get())
                obs = ent["observaciones"].get()
                quien_txt = quien.get()

                # Recuperar saldo actual para dejarlo igual
                saldo_actual, _ = obtener_datos_cliente(cid)

                datos = {
                    "numero_recibo": rec,
                    "id_cliente": cid,
                    "fecha_pago": datetime.today().strftime('%Y-%m-%d'),
                    "abono_parcial": val,
                    "saldo_restante": saldo_actual,  # saldo no cambia
                    "observaciones": obs,
                    "consigno_a": quien_txt
                }

                confirm_msg = (
                    f"Nº Recibo: {rec}\n"
                    f"ID Cliente: {cid}\n"
                    f"Valor Parcial: ${val:,.2f}\n"
                    f"Saldo (sin cambios): ${saldo_actual:,.2f}\n"
                    f"Consignó a: {quien_txt}\n\n"
                    "¿Registrar este abono parcial sin afectar saldo ni pago_hasta?"
                )
                if messagebox.askokcancel("Confirmar Pago Parcial", confirm_msg):
                    registrar_abono_parcial(datos)
                    messagebox.showinfo("Listo", "Pago parcial registrado correctamente.")
                    ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(
            ventana,
            text="Confirmar Pago Parcial",
            command=confirmar_parcial
        ).pack(pady=20)


    # botones principales
    tk.Button(raiz, text="Registrar Interés", width=30,
              command=lambda: abrir_registro("interes")).pack(pady=5)
    tk.Button(raiz, text="Registrar Abono", width=30,
              command=lambda: abrir_registro("abono")).pack(pady=5)
    tk.Button(raiz, text="Registrar Pago Parcial", width=30,
              command=abrir_pago_parcial).pack(pady=5)
    tk.Button(raiz, text="Ver Clientes", width=30,
              command=lambda: (raiz.destroy(), crear_vista_general())).pack(pady=5)

    raiz.mainloop()
