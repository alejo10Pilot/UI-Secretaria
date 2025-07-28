import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dateutil.relativedelta import relativedelta
import customtkinter as ctk

from db import (
    obtener_datos_cliente,
    obtener_nombre_cliente,
    calcular_interes,
    registrar_interes,
    registrar_abono,
    registrar_abono_parcial,
    obtener_todos_los_clientes,
    obtener_ultimo_pago_hasta_por_interes,
    obtener_id_cliente_por_registro
)

def mostrar_confirmacion(titulo, resumen):
    ctk.set_appearance_mode("light")  
    ctk.set_default_color_theme("blue")  

    ventana = ctk.CTkToplevel()
    ventana.title(titulo)
    ventana.geometry("480x550")
    ventana.resizable(False, False)
    ventana.grab_set()

    # Frame principal con bordes redondeados
    frame = ctk.CTkFrame(ventana, corner_radius=20)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    # Título
    titulo_label = ctk.CTkLabel(frame, text="Confirmar Datos", font=("Helvetica Neue", 20, "bold"))
    titulo_label.pack(pady=(20, 15))

    # Contenedor sin scroll (solo labels)
    datos_frame = ctk.CTkFrame(frame, fg_color="transparent")
    datos_frame.pack(padx=15, pady=10, fill="both", expand=True)

    for linea in resumen.split("\n"):
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            fila = ctk.CTkFrame(datos_frame, fg_color="transparent")
            fila.pack(fill="x", pady=5)

            clave_label = ctk.CTkLabel(
                fila, text=clave.strip() + ":", width=140,
                anchor="w", font=("Helvetica Neue", 13, "bold")
            )
            clave_label.pack(side="left", padx=(5, 10))

            valor_label = ctk.CTkLabel(
                fila, text=valor.strip(),
                anchor="w", font=("Helvetica Neue", 13)
            )
            valor_label.pack(side="left", fill="x", expand=True)
        elif linea.strip():
            ctk.CTkLabel(datos_frame, text=linea.strip(), font=("Helvetica Neue", 13)).pack(anchor="w", pady=2)

    # Frame de botones
    botones_frame = ctk.CTkFrame(frame, fg_color="transparent")
    botones_frame.pack(pady=(20, 15))

    confirmado = {"valor": False}

    def confirmar():
        confirmado["valor"] = True
        ventana.destroy()

    def cancelar():
        ventana.destroy()

    cancelar_btn = ctk.CTkButton(
        botones_frame, text="Cancelar", command=cancelar,
        width=120, height=35, fg_color="#f44336", hover_color="#e53935", font=("Helvetica Neue", 13, "bold")
        )
    cancelar_btn.pack(side="left", padx=15)

    confirmar_btn = ctk.CTkButton(
        botones_frame, text="Confirmar", command=confirmar,
        width=120, height=35, fg_color="#4CAF50", hover_color="#45a049", font=("Helvetica Neue", 13, "bold")
    )
    confirmar_btn.pack(side="left", padx=15)

    ventana.wait_window()
    return confirmado["valor"]









def crear_vista_general():
    raiz = tk.Tk()
    raiz.title("Vista General de Clientes")
    raiz.geometry("1000x500")

    cols = ("Carpeta", "Nombre", "Saldo", "Último Pago", "Pago Hasta")
    tabla = ttk.Treeview(raiz, columns=cols, show="headings")
    for col in cols:
        tabla.heading(col, text=col)
        tabla.column(col, anchor="center")
    tabla.pack(expand=True, fill="both", padx=10, pady=10)

    for c in obtener_todos_los_clientes():
        tabla.insert('', 'end', values=(
            c[1],
            c[2],
            f"${c[3]:,.2f}",
            c[4],
            c[5]
        ))

    tk.Button(raiz, text="Modificar", command=lambda: (raiz.destroy(), crear_ventana())).pack(pady=10)
    raiz.mainloop()


def crear_ventana():
    raiz = tk.Tk()
    raiz.title("Sistema de Registro")
    raiz.geometry("400x600")

    def abrir_registro(tipo):
        ventana = tk.Toplevel(raiz)
        ventana.title(f"Registrar {tipo.capitalize()}")
        ventana.geometry("400x500")

        campos = {
            "numero_recibo": "Número de Recibo",
            "id_cliente":    "Registro Carpeta",
            "fecha_pago":    "Fecha Pago (YYYY-MM-DD)",
            "observaciones": "Observaciones"
        }
        ent = {}
        for k, lbl in campos.items():
            tk.Label(ventana, text=lbl).pack()
            e = tk.Entry(ventana)
            if k == "fecha_pago":
                e.insert(0, datetime.today().strftime('%Y-%m-%d'))
            e.pack()
            ent[k] = e

        if tipo == "interes":
            tk.Label(ventana, text="Seleccione % interés").pack()
            pct = tk.StringVar(value="1.8%")
            cb = ttk.Combobox(ventana, textvariable=pct, values=["1.8%", "2%", "2.2%"])
            cb.pack()
            tk.Label(ventana, text="¿Meses?").pack()
            meses_var = tk.IntVar(value=1)
            tk.Spinbox(ventana, from_=1, to=12, textvariable=meses_var, width=5).pack()
            tk.Label(ventana, text="Ajuste (+ o -)").pack()
            ajuste_entry = tk.Entry(ventana)
            ajuste_entry.insert(0, "0")
            ajuste_entry.pack()
        else:
            tk.Label(ventana, text="Abono a capital").pack()
            abx = tk.Entry(ventana)
            abx.insert(0, "0")
            abx.pack()

        tk.Label(ventana, text="Consignó a:").pack()
        quien = tk.StringVar(value="Efectivo")
        cons = ttk.Combobox(
            ventana, textvariable=quien,
            values=["Efectivo","Alejo","Maria","Carlos","Andrea","Angela"]
        )
        cons.pack()

        def confirmar():
            registro = int(ent["id_cliente"].get())
            cid = obtener_id_cliente_por_registro(registro)
            saldo, pago_hasta_cliente, ajuste_pendiente = obtener_datos_cliente(cid)

            fecha_str = ent["fecha_pago"].get()
            fecha_usuario = datetime.strptime(fecha_str, "%Y-%m-%d")
            base = datetime.combine(pago_hasta_cliente, datetime.min.time()) if pago_hasta_cliente else fecha_usuario

            monto = 0
            resumen = ""
            ajuste_restante = 0.0  # Lo que quedará guardado después de este pago

            if tipo == "interes":
                porcentaje = float(pct.get().replace('%', '')) / 100
                m = max(1, int(meses_var.get()))
                monto_calculado = calcular_interes(saldo, porcentaje) * m

                # Leer ajuste adicional (+ o -)
                try:
                    ajuste_nuevo = float(ajuste_entry.get()) if ajuste_entry.get().strip() != "" else 0.0
                except:
                    ajuste_nuevo = 0.0

                # Ajuste total disponible (saldo a favor previo + nuevo ajuste)
                ajuste_total = ajuste_pendiente + ajuste_nuevo

                # Calcular monto real aplicando saldo a favor
                monto_real = monto_calculado - ajuste_total  # restamos saldo a favor

                # Determinar ajuste restante (si se usó todo o queda algo)
                if monto_real < 0:
                    # Se usó menos del saldo a favor, queda un nuevo saldo pendiente
                    ajuste_restante = abs(monto_real)
                    monto_real = 0.0  # no hay que pagar nada
                else:
                    ajuste_restante = 0.0  # ya se usó todo el ajuste

                nuevo_fecha = (base + relativedelta(months=m)).date()

                obs_extra = ""
                if ajuste_restante > 0:
                    obs_extra = f"\nSaldo a favor del cliente: ${ajuste_restante:,.2f}"

                resumen = (
                    f"RECIBO: {ent['numero_recibo'].get()}\n"
                    f"NOMBRE: {obtener_nombre_cliente(cid)}\n"
                    f"FECHA: {fecha_str}\n"
                    f"MESES: {m}\n"
                    f"PAGO HASTA: {nuevo_fecha}\n"
                    f"MONTO PAGADO: ${monto_real:,.2f}\n"
                    f"SALDO RESTANTE: ${saldo:,.2f}\n"
                    f"CONSIGNÓ A: {quien.get()}\n"
                    f"OBSERVACIONES: {ent['observaciones'].get()}{obs_extra}"
                )

                monto = monto_real

            else:
                ab = float(abx.get())
                nuevo_saldo = saldo - ab
                monto = ab
                resumen = (
                    f"NOMBRE: {obtener_nombre_cliente(cid)}\n"
                    f"RECIBO: {ent['numero_recibo'].get()}\n"
                    f"FECHA: {fecha_str}\n"
                    f"ABONO: ${ab:,.2f}\n"
                    f"NUEVO SALDO: ${nuevo_saldo:,.2f}\n"
                    f"TIPO: abono\n"
                    f"OBS: {ent['observaciones'].get()}\n"
                    f"CONSIGNÓ A: {quien.get()}"
                )

            if mostrar_confirmacion("Confirmar datos", resumen):
                datos = {
                    "numero_recibo": ent['numero_recibo'].get(),
                    "id_cliente": cid,
                    "registro_carpeta": registro,
                    "fecha_pago": fecha_str,
                    "observaciones": ent['observaciones'].get(),
                    "consigno_a": quien.get()
                }
                if tipo == "interes":
                    datos.update({
                        "pago_hasta": nuevo_fecha,
                        "abono_intereses": monto,
                        "saldo_restante": saldo,
                        "ajuste_pendiente": ajuste_restante  # se actualiza correctamente
                    })
                    registrar_interes(datos)
                else:
                    if tipo == "abono":
                        datos.update({
                            "abono_capital": monto,
                            "saldo_restante": nuevo_saldo
                        })
                        registrar_abono(datos)
                ventana.destroy()

        tk.Button(ventana, text="Confirmar", command=confirmar).pack(pady=10)

    def abrir_pago_parcial():
        ventana = tk.Toplevel(raiz)
        ventana.title("Registrar Pago Parcial")
        ventana.geometry("500x500")

        campos = {
            "numero_recibo": "Número de Recibo",
            "id_cliente": "Registro Carpeta",
            "fecha_pago": "Fecha Pago (YYYY-MM-DD)",
            "valor": "Valor Parcial ($)",
            "observaciones": "Observaciones"
        }
        ent = {}
        for k, lbl in campos.items():
            tk.Label(ventana, text=lbl).pack(pady=(10, 0))
            e = tk.Entry(ventana)
            if k == "valor":
                e.insert(0, "0")
            if k == "fecha_pago":
                e.insert(0, datetime.today().strftime('%Y-%m-%d'))
            e.pack()
            ent[k] = e

        tk.Label(ventana, text="Consignó a:").pack(pady=(10, 0))
        quien = tk.StringVar(value="Efectivo")
        cons = ttk.Combobox(
            ventana,
            textvariable=quien,
            values=["Efectivo", "Alejo", "Maria", "Carlos", "Andrea", "Angela"],
            state="readonly"
        )
        cons.pack()
        
        def confirmar_parcial():
            try:
                rec = ent['numero_recibo'].get()
                registro = int(ent['id_cliente'].get())
                fecha_str = ent['fecha_pago'].get()
                cid = obtener_id_cliente_por_registro(registro)
                val = float(ent['valor'].get())
                obs = ent['observaciones'].get()
                quien_txt = quien.get()
                saldo_actual, _ = obtener_datos_cliente(cid)
                datos = {
                    'numero_recibo': rec,
                    'id_cliente': cid,
                    'registro_carpeta': registro,
                    'fecha_pago': fecha_str,
                    'abono_parcial': val,
                    'saldo_restante': saldo_actual,
                    'observaciones': obs,
                    'consigno_a': quien_txt
                }
                confirm_msg = (
                    f"Nº Recibo: {rec}\nRegistro Carpeta: {registro}\nFecha: {fecha_str}\n"
                    f"Valor Parcial: ${val:,.2f}\nSaldo (sin cambios): ${saldo_actual:,.2f}\n"
                    f"Consignó a: {quien_txt}\n\n¿Registrar este abono parcial sin afectar saldo ni pago_hasta?"
                )
                if messagebox.askokcancel("Confirmar Pago Parcial", confirm_msg):
                    registrar_abono_parcial(datos)
                    messagebox.showinfo("Listo", "Pago parcial registrado correctamente.")
                    ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(ventana, text="Confirmar Pago Parcial", command=confirmar_parcial).pack(pady=20)

    raiz_buttons=[("Registrar Interés",lambda:abrir_registro("interes")),("Registrar Abono",lambda:abrir_registro("abono")),("Registrar Pago Parcial",abrir_pago_parcial),("Ver Clientes",lambda:(raiz.destroy(),crear_vista_general()))]
    for text,cmd in raiz_buttons:
        tk.Button(raiz,text=text,width=30,command=cmd).pack(pady=5)
    raiz.mainloop()
