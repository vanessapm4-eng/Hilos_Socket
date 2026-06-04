import socket
import json
import threading
import tkinter as tk
from tkinter import messagebox

HOST = 'localhost'
PORT = 5000

TAMANIO_CELDA = 36
COLORES_PALABRAS = [
    "#409138", "#975594", "#c7962e", "#7a2add", "#C53B62",
    "#be7141", "#198f7b", "#5d85c7", "#2d3255", "#773A45",
    "#4e5a8b", "#396275", '#d20f39', '#40a02b', '#fe640b'
]

#  Pantalla de nombre 

def pedir_nombre():
    ventana = tk.Tk()
    ventana.title("Sopa de Letras")
    ventana.configure(bg='#1e1e2e')
    ventana.resizable(False, False)

    tk.Label(ventana, text="✏  Ingresa tu nombre:",
             bg='#1e1e2e', fg='#cdd6f4',
             font=('Courier', 11)).pack(pady=(24, 6), padx=40)

    entrada = tk.Entry(ventana, font=('Courier', 12),
                       bg='#313244', fg='#cdd6f4',
                       insertbackground='white', relief='flat',
                       justify='center')
    entrada.pack(pady=(0, 12), padx=40)
    entrada.focus()

    nombre = tk.StringVar()

    def confirmar():
        n = entrada.get().strip()
        if n:
            nombre.set(n)
            ventana.destroy()

    tk.Button(ventana, text="  Jugar  ",
              bg='#89b4fa', fg='#1e1e2e',
              font=('Courier', 10, 'bold'), relief='flat',
              cursor='hand2', command=confirmar).pack(pady=(0, 24))

    ventana.bind('<Return>', lambda e: confirmar())
    ventana.mainloop()
    return nombre.get() or "Jugador"


# Clase principal 

class SopaLetras:
    def __init__(self, root, nombre):
        self.root   = root
        self.nombre = nombre
        self.root.title(f"Sopa de Letras — {self.nombre}")
        self.root.configure(bg='#1e1e2e')
        self.root.resizable(False, False)

        self.tablero             = []
        self.palabras            = []
        self.encontradas         = {}
        self.resueltas           = {}
        self.seleccion           = []
        self.inicio_sel          = None
        self.posiciones_solucion = {}
        self.segundos            = 0
        self.timer_activo        = False

        # Conexión al servidor
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((HOST, PORT))
            print("Conectado al servidor")
        except ConnectionRefusedError:
            messagebox.showerror("Error",
                "No se pudo conectar al servidor.\n"
                "Asegúrate de que servidor.js esté corriendo.")
            root.destroy()
            return

        threading.Thread(target=self.escuchar, daemon=True).start()
        self.construir_ui()
        self.enviar({"accion": "iniciar"})

    #  Comunicación

    def enviar(self, datos):
        try:
            self.sock.send((json.dumps(datos) + '\n').encode())
        except Exception as e:
            print(f"Error al enviar: {e}")

    def escuchar(self):
        buffer = ''
        while True:
            try:
                data = self.sock.recv(8192).decode()
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    linea, buffer = buffer.split('\n', 1)
                    if linea.strip():
                        self.procesar_mensaje(json.loads(linea))
            except Exception as e:
                print(f"Error al recibir: {e}")
                break

    def procesar_mensaje(self, msg):
        if msg['tipo'] == 'tablero':
            self.tablero  = msg['tablero']
            self.palabras = msg['palabras']
            self.root.after(0, self.dibujar_todo)

        elif msg['tipo'] == 'solucion':
            self.posiciones_solucion = msg['posiciones']
            self.root.after(0, self.mostrar_solucion)

        elif msg['tipo'] == 'ranking_guardado':
            print("Puntaje guardado en servidor")

        elif msg['tipo'] == 'ranking':
            self.root.after(0, lambda: self.mostrar_ventana_ranking(msg['datos']))

    # Interfaz

    def construir_ui(self):
        self.frame = tk.Frame(self.root, bg='#1e1e2e', padx=12, pady=12)
        self.frame.pack()

        tk.Label(self.frame, text="SOPA DE LETRAS — PROFESIONES",
                 bg='#1e1e2e', fg='#cdd6f4',
                 font=('Courier', 13, 'bold')).grid(
                 row=0, column=0, columnspan=2, pady=(0, 8))

        ctrl = tk.Frame(self.frame, bg='#1e1e2e')
        ctrl.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 8))

        self.lbl_timer = tk.Label(ctrl, text="⏱ 00:00",
                                   bg='#1e1e2e', fg='#a6e3a1',
                                   font=('Courier', 11, 'bold'))
        self.lbl_timer.pack(side='left')

        tk.Button(ctrl, text="  🏆 Ranking  ",
                  bg='#313244', fg='#f9e2af', activebackground='#45475a',
                  font=('Courier', 9), relief='flat', cursor='hand2',
                  command=self.pedir_ranking).pack(side='right', padx=(4, 0))

        tk.Button(ctrl, text="  Resolver  ",
                  bg='#313244', fg='#f38ba8', activebackground='#45475a',
                  font=('Courier', 9), relief='flat', cursor='hand2',
                  command=self.pedir_solucion).pack(side='right', padx=(4, 0))

        tk.Button(ctrl, text="  Nuevo juego  ",
                  bg='#313244', fg='#cdd6f4', activebackground='#45475a',
                  font=('Courier', 9), relief='flat', cursor='hand2',
                  command=self.nuevo_juego).pack(side='right')

        tam = TAMANIO_CELDA * 15
        self.canvas = tk.Canvas(self.frame, width=tam, height=tam,
                                 bg='#181825', highlightthickness=0)
        self.canvas.grid(row=2, column=0, padx=(0, 12))
        self.canvas.bind('<ButtonPress-1>',   self.click_inicio)
        self.canvas.bind('<B1-Motion>',       self.click_movimiento)
        self.canvas.bind('<ButtonRelease-1>', self.click_fin)

        panel = tk.Frame(self.frame, bg='#1e1e2e')
        panel.grid(row=2, column=1, sticky='n')

        tk.Label(panel, text="PALABRAS", bg='#1e1e2e', fg='#89b4fa',
                 font=('Courier', 10, 'bold')).pack(anchor='w', pady=(0, 6))

        self.labels_palabras = {}
        for p in ['TRADUCTOR','CAMARERA','EMPLEADO','RELOJERO','APICULTOR',
                  'ATLETA','ASTRONAUTA','CONDUCTOR','JOYERO','CIRUJANO',
                  'FOTOGRAFO','MODISTA','GEOLOGO','JUEZ','MODELO']:
            lbl = tk.Label(panel, text=p, bg='#1e1e2e', fg='#cdd6f4',
                           font=('Courier', 9), anchor='w', width=12)
            lbl.pack(anchor='w')
            self.labels_palabras[p] = lbl

        self.lbl_estado = tk.Label(self.frame, text="Generando tablero...",
                                    bg='#1e1e2e', fg='#6c7086',
                                    font=('Courier', 9))
        self.lbl_estado.grid(row=3, column=0, columnspan=2, pady=(6, 0))

    # Dibujo 

    def dibujar_todo(self):
        self.encontradas.clear()
        self.resueltas.clear()
        self.seleccion.clear()
        self.inicio_sel = None
        self.posiciones_solucion.clear()

        for lbl in self.labels_palabras.values():
            lbl.config(fg='#cdd6f4', font=('Courier', 9))

        self.canvas.delete('all')
        self.dibujar_tablero()
        self.segundos = 0
        self.timer_activo = True
        self.actualizar_timer()
        self.lbl_estado.config(
            text="Haz clic y arrastra para seleccionar una palabra")

    def dibujar_tablero(self):
        self.canvas.delete('all')
        tc = TAMANIO_CELDA

        todas = {**self.resueltas, **self.encontradas}
        for palabra, color in todas.items():
            for (f, c) in self.posiciones_solucion.get(palabra, []):
                x1, y1 = c*tc+2, f*tc+2
                self.canvas.create_rectangle(x1, y1, x1+tc-2, y1+tc-2,
                                              fill=color, outline='')

        for (f, c) in self.seleccion:
            x1, y1 = c*tc+2, f*tc+2
            self.canvas.create_rectangle(x1, y1, x1+tc-2, y1+tc-2,
                                          fill='#45475a', outline='')

        for f in range(15):
            for c in range(15):
                if f < len(self.tablero) and c < len(self.tablero[f]):
                    self.canvas.create_text(
                        c*tc + tc//2, f*tc + tc//2,
                        text=self.tablero[f][c],
                        fill='#cdd6f4',
                        font=('Courier', 13, 'bold'))

    #  Selección 

    def celda_desde_xy(self, x, y):
        f, c = y // TAMANIO_CELDA, x // TAMANIO_CELDA
        return (f, c) if 0 <= f < 15 and 0 <= c < 15 else None

    def celdas_en_linea(self, inicio, fin):
        f1, c1 = inicio
        f2, c2 = fin
        df, dc = f2-f1, c2-c1
        pasos = max(abs(df), abs(dc))
        if pasos == 0:
            return [inicio]
        if df != 0 and dc != 0 and abs(df) != abs(dc):
            return [inicio]
        sf = 0 if df == 0 else df // abs(df)
        sc = 0 if dc == 0 else dc // abs(dc)
        return [(f1+i*sf, c1+i*sc) for i in range(pasos+1)]

    def click_inicio(self, event):
        celda = self.celda_desde_xy(event.x, event.y)
        if celda:
            self.inicio_sel = celda
            self.seleccion  = [celda]
            self.dibujar_tablero()

    def click_movimiento(self, event):
        if not self.inicio_sel:
            return
        celda = self.celda_desde_xy(event.x, event.y)
        if celda:
            self.seleccion = self.celdas_en_linea(self.inicio_sel, celda)
            self.dibujar_tablero()

    def click_fin(self, event):
        if len(self.seleccion) < 2:
            self.seleccion  = []
            self.inicio_sel = None
            self.dibujar_tablero()
            return

        palabra     = ''.join(self.tablero[f][c] for (f, c) in self.seleccion)
        palabra_rev = palabra[::-1]

        encontrada = None
        for p in self.palabras:
            if (p == palabra or p == palabra_rev) \
               and p not in self.encontradas \
               and p not in self.resueltas:
                encontrada = p
                break

        if encontrada:
            idx   = list(self.labels_palabras.keys()).index(encontrada)
            color = COLORES_PALABRAS[idx % len(COLORES_PALABRAS)]
            self.encontradas[encontrada]         = color
            self.posiciones_solucion[encontrada] = self.seleccion[:]
            self.labels_palabras[encontrada].config(
                fg=color, font=('Courier', 9, 'overstrike'))
            self.lbl_estado.config(text=f'¡Encontraste "{encontrada}"!')
            self.enviar({"accion": "verificar", "palabra": encontrada})

            if len(self.encontradas) + len(self.resueltas) == len(self.palabras):
                self.root.after(300, self.juego_terminado)

        self.seleccion  = []
        self.inicio_sel = None
        self.dibujar_tablero()

    #  Fin de juego 

    def juego_terminado(self):
        self.timer_activo = False
        tiempo_txt = self.lbl_timer.cget("text")[2:]
        self.lbl_estado.config(text="¡Puntaje guardado!")

        self.enviar({
            "accion":      "guardar_puntaje",
            "nombre":      self.nombre,
            "tiempo":      self.segundos,
            "encontradas": len(self.encontradas)
        })

        win = tk.Toplevel(self.root)
        win.title("¡Felicitaciones!")
        win.configure(bg='#1e1e2e')
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="🎉", bg='#1e1e2e',
                 font=('Courier', 60)).pack(pady=(28, 0))

        tk.Label(win, text="¡FELICITACIONES!",
                 bg='#1e1e2e', fg='#f9e2af',
                 font=('Courier', 20, 'bold')).pack(pady=(4, 0))

        tk.Label(win, text=self.nombre,
                 bg='#1e1e2e', fg='#89b4fa',
                 font=('Courier', 15, 'bold')).pack(pady=(6, 0))

        tk.Label(win, text="completaste todas las palabras",
                 bg='#1e1e2e', fg='#cdd6f4',
                 font=('Courier', 11)).pack(pady=(2, 0))

        tk.Label(win, text=f"⏱  Tiempo: {tiempo_txt}",
                 bg='#1e1e2e', fg='#a6e3a1',
                 font=('Courier', 14, 'bold')).pack(pady=(18, 0))

        tk.Frame(win, bg='#313244', height=1).pack(
            fill='x', padx=30, pady=16)

        tk.Button(win, text="  🏆 Ver Ranking  ",
                  bg='#f9e2af', fg='#1e1e2e',
                  font=('Courier', 11, 'bold'), relief='flat',
                  cursor='hand2', padx=10, pady=6,
                  command=lambda: [win.destroy(), self.pedir_ranking()]
                  ).pack(pady=(0, 8))

        tk.Button(win, text="  Nuevo juego  ",
                  bg='#313244', fg='#cdd6f4',
                  font=('Courier', 10), relief='flat',
                  cursor='hand2', padx=10, pady=4,
                  command=lambda: [win.destroy(), self.nuevo_juego()]
                  ).pack(pady=(0, 28))

    # Ranking 

    def pedir_ranking(self):
        self.enviar({"accion": "ver_ranking"})

    def mostrar_ventana_ranking(self, datos):
        win = tk.Toplevel(self.root)
        win.title("🏆 Ranking")
        win.configure(bg='#1e1e2e')
        win.resizable(False, False)

        tk.Label(win, text="🏆  TOP JUGADORES",
                 bg='#1e1e2e', fg='#f9e2af',
                 font=('Courier', 13, 'bold')).pack(pady=(18, 8), padx=30)

        if not datos:
            tk.Label(win, text="Aún no hay puntajes registrados.",
                     bg='#1e1e2e', fg='#6c7086',
                     font=('Courier', 9)).pack(pady=(0, 16), padx=30)
        else:
            encabezado = f"{'#':<3} {'Nombre':<14} {'Tiempo':>7}  {'Palabras':>8}"
            tk.Label(win, text=encabezado, bg='#1e1e2e', fg='#89b4fa',
                     font=('Courier', 9, 'bold')).pack(anchor='w', padx=20)

            tk.Frame(win, bg='#313244', height=1).pack(fill='x', padx=20, pady=3)

            for i, d in enumerate(datos, 1):
                m = d['tiempo'] // 60
                s = d['tiempo'] % 60
                linea = (f"{i:<3} {d['nombre']:<14} "
                         f"{m:02}:{s:02}     {d['encontradas']:>4}/15")
                color = '#f9e2af' if i == 1 else '#cdd6f4'
                tk.Label(win, text=linea, bg='#1e1e2e', fg=color,
                         font=('Courier', 9)).pack(anchor='w', padx=20)

        tk.Button(win, text="  Cerrar  ",
                  bg='#313244', fg='#cdd6f4',
                  font=('Courier', 9), relief='flat',
                  cursor='hand2', command=win.destroy).pack(pady=16)

    # Solución 

    def pedir_solucion(self):
        self.enviar({"accion": "resolver"})

    def mostrar_solucion(self):
        self.timer_activo = False
        for palabra, celdas in self.posiciones_solucion.items():
            if palabra not in self.encontradas:
                idx   = list(self.labels_palabras.keys()).index(palabra)
                color = COLORES_PALABRAS[idx % len(COLORES_PALABRAS)]
                self.resueltas[palabra] = color
                self.labels_palabras[palabra].config(
                    fg='#f38ba8', font=('Courier', 9, 'overstrike'))
        self.lbl_estado.config(text="Solución mostrada")
        self.dibujar_tablero()

    # Timer 

    def actualizar_timer(self):
        if self.timer_activo:
            self.segundos += 1
            m, s = self.segundos // 60, self.segundos % 60
            self.lbl_timer.config(text=f"⏱ {m:02}:{s:02}")
            self.root.after(1000, self.actualizar_timer)

    # Nuevo juego 

    def nuevo_juego(self):
        self.timer_activo = False
        self.segundos     = 0
        self.lbl_timer.config(text="⏱ 00:00")
        self.posiciones_solucion.clear()
        self.lbl_estado.config(text="Generando tablero...")
        self.enviar({"accion": "iniciar"})


# Main

nombre_jugador = pedir_nombre()
root = tk.Tk()
app  = SopaLetras(root, nombre_jugador)
root.mainloop()