import http from 'http';
import { createReadStream, promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'data', 'records.json');
const PUBLIC_DIR = path.join(__dirname, 'public');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
};

async function ensureDataFile() {
  try {
    await fs.access(DATA_FILE);
  } catch (error) {
    await fs.mkdir(path.dirname(DATA_FILE), { recursive: true });
    await fs.writeFile(DATA_FILE, JSON.stringify([]));
  }
}

async function readRecords() {
  await ensureDataFile();
  const content = await fs.readFile(DATA_FILE, 'utf-8');
  return JSON.parse(content);
}

async function writeRecords(records) {
  await fs.writeFile(DATA_FILE, JSON.stringify(records, null, 2));
}

function setCorsHeaders(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

async function handleApiRequest(req, res, pathname) {
  setCorsHeaders(res);

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method === 'GET' && pathname === '/api/records') {
    try {
      const records = await readRecords();
      res.writeHead(200, { 'Content-Type': MIME_TYPES['.json'] });
      res.end(JSON.stringify({ records }));
    } catch (error) {
      console.error('Error al leer registros', error);
      res.writeHead(500, { 'Content-Type': MIME_TYPES['.json'] });
      res.end(JSON.stringify({ message: 'No se pudieron obtener los registros.' }));
    }
    return;
  }

  if (req.method === 'POST' && pathname === '/api/records') {
    try {
      const body = await readRequestBody(req);
      const { entries } = JSON.parse(body || '{}');

      if (!Array.isArray(entries)) {
        res.writeHead(400, { 'Content-Type': MIME_TYPES['.json'] });
        res.end(JSON.stringify({ message: 'El cuerpo de la petición debe incluir un arreglo "entries".' }));
        return;
      }

      const records = await readRecords();
      const merged = [...records];

      entries.forEach((entry) => {
        const exists = merged.some((record) => record.id === entry.id);
        if (!exists) {
          merged.push({ ...entry, syncedAt: new Date().toISOString() });
        }
      });

      await writeRecords(merged);

      res.writeHead(201, { 'Content-Type': MIME_TYPES['.json'] });
      res.end(
        JSON.stringify({
          message: 'Registros sincronizados correctamente.',
          syncedCount: merged.length - records.length,
        }),
      );
    } catch (error) {
      if (error instanceof SyntaxError) {
        res.writeHead(400, { 'Content-Type': MIME_TYPES['.json'] });
        res.end(JSON.stringify({ message: 'El cuerpo de la petición debe ser JSON válido.' }));
        return;
      }

      console.error('Error al guardar registros', error);
      res.writeHead(500, { 'Content-Type': MIME_TYPES['.json'] });
      res.end(JSON.stringify({ message: 'No se pudieron guardar los registros.' }));
    }
    return;
  }

  res.writeHead(404, { 'Content-Type': MIME_TYPES['.json'] });
  res.end(JSON.stringify({ message: 'Recurso no encontrado.' }));
}

function readRequestBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';

    req.on('data', (chunk) => {
      data += chunk;
    });

    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

async function serveStaticFile(res, filePath) {
  try {
    const stats = await fs.stat(filePath);
    if (stats.isDirectory()) {
      return serveStaticFile(res, path.join(filePath, 'index.html'));
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, { 'Content-Type': contentType });
    const stream = createReadStream(filePath);
    stream.pipe(res);
    stream.on('error', (error) => {
      console.error('Error al leer archivo estático', error);
      res.writeHead(500, { 'Content-Type': MIME_TYPES['.html'] });
      res.end('<h1>500 - Error interno del servidor</h1>');
    });
  } catch (error) {
    if (error.code === 'ENOENT') {
      const fallback = path.join(PUBLIC_DIR, 'index.html');
      if (filePath !== fallback) {
        serveStaticFile(res, fallback);
        return;
      }

      res.writeHead(404, { 'Content-Type': MIME_TYPES['.html'] });
      res.end('<h1>404 - Recurso no encontrado</h1>');
    } else {
      console.error('Error al servir archivo estático', error);
      res.writeHead(500, { 'Content-Type': MIME_TYPES['.html'] });
      res.end('<h1>500 - Error interno del servidor</h1>');
    }
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;

  if (pathname.startsWith('/api/')) {
    await handleApiRequest(req, res, pathname);
    return;
  }

  let requestedPath = pathname === '/' ? path.join(PUBLIC_DIR, 'index.html') : path.join(PUBLIC_DIR, pathname);

  if (!requestedPath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403, { 'Content-Type': MIME_TYPES['.html'] });
    res.end('<h1>403 - Acceso denegado</h1>');
    return;
  }

  serveStaticFile(res, requestedPath);
});

server.listen(PORT, () => {
  console.log(`Servidor iniciado en http://localhost:${PORT}`);
});
