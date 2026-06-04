const { parentPort } = require('worker_threads');
const fs = require('fs');

const ARCHIVO = 'ranking.json';

function leerRanking() {
  if (!fs.existsSync(ARCHIVO)) return [];
  const contenido = fs.readFileSync(ARCHIVO, 'utf-8');
  return JSON.parse(contenido);
}

function guardarRanking(ranking) {
  fs.writeFileSync(ARCHIVO, JSON.stringify(ranking, null, 2));
}
// recibe el puntaje a guardar y lo guarda en el archivo, o lee el ranking completo y lo envia al servidor para que lo envie al cliente que lo solicito
parentPort.on('message', (msg) => {
  if (msg.accion === 'guardar') {
    const ranking = leerRanking();
    ranking.push({
      nombre:     msg.nombre,
      tiempo:     msg.tiempo,
      encontradas: msg.encontradas,
      fecha:      new Date().toLocaleString()
    });
    ranking.sort((a, b) => b.encontradas - a.encontradas || a.tiempo - b.tiempo);
    guardarRanking(ranking);
    parentPort.postMessage({ tipo: 'guardado', ok: true });
  }

  if (msg.accion === 'leer') {
    const ranking = leerRanking();
    parentPort.postMessage({ tipo: 'ranking', datos: ranking.slice(0, 10) });
  }
});