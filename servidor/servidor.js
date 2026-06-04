const net    = require('net');
const { Worker } = require('worker_threads');
const path   = require('path');

const PORT    = 5000;
const TAMANIO = 15;
const LETRAS  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

const PALABRAS = [
  'TRADUCTOR', 'CAMARERA', 'EMPLEADO', 'RELOJERO', 'APICULTOR',
  'ATLETA', 'ASTRONAUTA', 'CONDUCTOR', 'JOYERO', 'CIRUJANO',
  'FOTOGRAFO', 'MODISTA', 'GEOLOGO', 'JUEZ', 'MODELO'
];

// Worker de Ranking (se crea una sola vez para manejar todas las solicitudes de ranking) 

let socketEsperandoRanking = null;

const workerRanking = new Worker(path.join(__dirname, 'rankingWorker.js')); 

workerRanking.on('message', (msg) => {
  if (msg.tipo === 'guardado') {
    console.log('[Ranking] Puntaje guardado correctamente');
  }
  if (msg.tipo === 'ranking') {
    console.log('[Ranking] Datos leídos:', msg.datos.length, 'registros');
    if (socketEsperandoRanking) {
      socketEsperandoRanking.write(
        JSON.stringify({ tipo: 'ranking', datos: msg.datos }) + '\n'
      );
      socketEsperandoRanking = null;
    }
  }
});

workerRanking.on('error', (err) => {
  console.log(`[Ranking] Error en worker: ${err.message}`);
});

// Funciones del tablero 

function crearTableroVacio() {
  return Array.from({ length: TAMANIO }, () => Array(TAMANIO).fill(''));
}

function rellenarAleatorio(tablero) {
  for (let f = 0; f < TAMANIO; f++)
    for (let c = 0; c < TAMANIO; c++)
      if (tablero[f][c] === '')
        tablero[f][c] = LETRAS[Math.floor(Math.random() * LETRAS.length)];
}
// worket nuevo por cada palabra 
function colocarPalabraConHilo(tablero, palabra) {
  return new Promise((resolve) => {
    const worker = new Worker(path.join(__dirname, 'wordWorker.js'), {
      workerData: {
        tablero: tablero.map(fila => [...fila]),
        palabra,
        tamanio: TAMANIO
      }
    });
    worker.on('message', (data) => {
      if (data.resultado) {
        const { f, c, df, dc } = data.resultado;
        const celdas = [];
        for (let i = 0; i < palabra.length; i++) {
          tablero[f + i * df][c + i * dc] = palabra[i];
          celdas.push([f + i * df, c + i * dc]);
        }
        resolve({ palabra, celdas });
      } else {
        resolve({ palabra, celdas: [] });
      }
    });
    worker.on('error', () => resolve({ palabra, celdas: [] }));
  });
}

async function generarTablero() {
  const tablero   = crearTableroVacio();
  const posiciones = {};
  const mezcladas = [...PALABRAS].sort(() => Math.random() - 0.5);

  for (const palabra of mezcladas) { // recorre la 15 palabras y por cada una lanza un hilo independiete 
    const resultado = await colocarPalabraConHilo(tablero, palabra);
    if (resultado.celdas.length > 0)
      posiciones[palabra] = resultado.celdas;
  }

  rellenarAleatorio(tablero);
  return { tablero, posiciones };
}

// Servidor TCP abre el worket y espera conexiones 

const server = net.createServer((socket) => {
  console.log(`[Servidor] Cliente conectado: ${socket.remoteAddress}:${socket.remotePort}`);

  let posiciones = {};
  let buffer     = '';

  socket.on('data', async (data) => {
    buffer += data.toString();

    while (buffer.includes('\n')) {
      const idx   = buffer.indexOf('\n');
      const linea = buffer.substring(0, idx).trim();
      buffer      = buffer.substring(idx + 1);

      if (!linea) continue;

      let mensaje;
      try {
        mensaje = JSON.parse(linea);
      } catch (e) {
        console.log('[Servidor] JSON inválido:', linea);
        continue;
      }

      console.log(`[Servidor] Acción recibida: ${mensaje.accion}`);

      // Iniciar juego 
      if (mensaje.accion === 'iniciar') {
        console.log('[Servidor] Generando tablero con hilos...');
        const resultado = await generarTablero();
        posiciones = resultado.posiciones;
        socket.write(JSON.stringify({
          tipo:    'tablero',
          tablero: resultado.tablero,
          palabras: PALABRAS
        }) + '\n');
        console.log('[Servidor] Tablero enviado');
      }

      // Verificar palabras
      if (mensaje.accion === 'verificar') {
        const encontrada = PALABRAS.includes(mensaje.palabra);
        socket.write(JSON.stringify({
          tipo:      'resultado',
          encontrada,
          palabra:   mensaje.palabra
        }) + '\n');
      }

      // Resolver 
      if (mensaje.accion === 'resolver') {
        socket.write(JSON.stringify({
          tipo:      'solucion',
          posiciones
        }) + '\n');
      }

      // Guardar puntaje y lo envia 
      if (mensaje.accion === 'guardar_puntaje') {
        console.log(`[Ranking] Guardando puntaje de: ${mensaje.nombre}`);
        workerRanking.postMessage({
          accion:      'guardar',
          nombre:      mensaje.nombre,
          tiempo:      mensaje.tiempo,
          encontradas: mensaje.encontradas
        });
        socket.write(JSON.stringify({ tipo: 'ranking_guardado' }) + '\n');
      }

      // Ver ranking 
      if (mensaje.accion === 'ver_ranking') {
        console.log('[Ranking] Solicitando datos al worker...');
        socketEsperandoRanking = socket;
        workerRanking.postMessage({ accion: 'leer' });
      }
    }
  });

  socket.on('end',   () => console.log('[Servidor] Cliente desconectado'));
  socket.on('error', (err) => console.log(`[Servidor] Error: ${err.message}`));
});

server.listen(PORT, () => {
  console.log(`[Servidor] Escuchando en puerto ${PORT}`);
});