# Sopa de Letras — Profesiones y Oficios
 
Juego de sopa de letras multijugador con arquitectura cliente-servidor
 
---
 
## Tecnologías
 
| Componente | Tecnología |
|---|---|
| Servidor | Node.js (módulos `net` y `worker_threads`) |
| Cliente | Python 3 + Tkinter |
| Comunicación | Socket TCP con protocolo JSON |
| Persistencia | Archivo `ranking.json` |
 
---
 
## Estructura del proyecto
 
```
sopa-letras/
├── servidor/
│   ├── servidor.js        # Servidor TCP principal
│   ├── wordWorker.js      # Hilo por cada palabra del tablero
│   └── rankingWorker.js   # Hilo dedicado al ranking
└── cliente/
    └── cliente.py         # Interfaz gráfica Tkinter
```
 
---
 
## Arquitectura
 
```
Cliente Python                 Servidor Node.js
──────────────                 ────────────────
  Tkinter UI                    net.createServer()
      │                               │
  socket TCP  ◄──── JSON ────►  socket TCP
      │                               │
  threading                     worker_threads
  (hilo escucha)            ┌────────┴────────┐
                        wordWorker      rankingWorker
                     (1 por palabra)   (ranking.json)
```
 
---
 
## Uso de Hilos
 
El proyecto implementa tres tipos de hilos:
 
**1. Worker por palabra (`wordWorker.js`)**
Cuando el servidor genera un tablero nuevo, crea un hilo independiente por cada una de las 15 palabras. Cada hilo busca una posición válida en el tablero probando hasta 500 combinaciones de fila, columna y dirección (8 posibles).
 
**2. Worker de Ranking (`rankingWorker.js`) — Trabajo independiente**
Hilo dedicado exclusivamente a leer y escribir el archivo `ranking.json`. El servidor le envía los puntajes con `postMessage()` sin bloquearse, permitiendo que el juego continúe mientras el archivo se escribe en disco.
 
**3. Hilo de escucha en el cliente (`cliente.py`)**
Python usa `threading.Thread` para escuchar mensajes del servidor en segundo plano, sin congelar la interfaz gráfica de Tkinter. Usa `root.after()` para pasar las actualizaciones al hilo principal de forma segura.
 
---
 
## Protocolo de comunicación
 
Mensajes en formato JSON separados por `\n`.
 
| Cliente envía | Servidor responde |
|---|---|
| `{"accion": "iniciar"}` | `{"tipo": "tablero", "tablero": [...], "palabras": [...]}` |
| `{"accion": "verificar", "palabra": "JUEZ"}` | `{"tipo": "resultado", "encontrada": true}` |
| `{"accion": "resolver"}` | `{"tipo": "solucion", "posiciones": {...}}` |
| `{"accion": "guardar_puntaje", ...}` | `{"tipo": "ranking_guardado"}` |
| `{"accion": "ver_ranking"}` | `{"tipo": "ranking", "datos": [...]}` |
 
---
 
## Instalación y ejecución
 
### Requisitos
- Node.js v14 o superior
- Python 3.8 o superior
### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/sopa-letras.git
cd sopa-letras
```
 
### 2. Iniciar el servidor
```bash
cd servidor
node servidor.js
```
 
### 3. Iniciar el cliente (en otra terminal)
```bash
cd cliente
python cliente.py
```
 
---
 
## Cómo jugar
 
1. Ingresa tu nombre al iniciar
2. Haz clic y arrastra sobre las letras para seleccionar una palabra
3. Las palabras pueden estar en cualquiera de las 8 direcciones
4. Usa el botón Resolver si necesitas ayuda
5. Al completar el juego tu puntaje se guarda automáticamente
6. Consulta el Ranking para ver los mejores jugadores
---
 
## Palabras del juego
 
`TRADUCTOR` · `CAMARERA` · `EMPLEADO` · `RELOJERO` · `APICULTOR` · `ATLETA` · `ASTRONAUTA` · `CONDUCTOR` · `JOYERO` · `CIRUJANO` · `FOTOGRAFO` · `MODISTA` · `GEOLOGO` · `JUEZ` · `MODELO`
 
---
 
##  Autora
 Vanessa Palacios 
 
