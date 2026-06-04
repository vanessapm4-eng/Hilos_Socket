const { workerData, parentPort } = require('worker_threads');

const DIRECCIONES = [
  [0, 1],   // derecha
  [0, -1],  // izquierda
  [1, 0],   // abajo
  [-1, 0],  // arriba
  [1, 1],   // diagonal ↘
  [1, -1],  // diagonal ↙
  [-1, 1],  // diagonal ↗
  [-1, -1]  // diagonal ↖
];

const { tablero, palabra, tamanio } = workerData;

function puedoColocar(f, c, df, dc) {
  for (let i = 0; i < palabra.length; i++) {
    const nf = f + i * df;
    const nc = c + i * dc;
    if (nf < 0 || nf >= tamanio || nc < 0 || nc >= tamanio) return false;
    if (tablero[nf][nc] !== '' && tablero[nf][nc] !== palabra[i]) return false;
  }
  return true;
}

let resultado = null;

for (let intento = 0; intento < 500 && !resultado; intento++) {
  const di = Math.floor(Math.random() * 8);
  const [df, dc] = DIRECCIONES[di];
  const f = Math.floor(Math.random() * tamanio);
  const c = Math.floor(Math.random() * tamanio);

  if (puedoColocar(f, c, df, dc)) {
    resultado = { f, c, df, dc };
  }
}

parentPort.postMessage({ palabra, resultado });