#!/usr/bin/env node
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

function resolvePython() {
  const candidates = process.platform === 'win32'
    ? [
        path.join(rootDir, '.venv', 'Scripts', 'python.exe'),
        'python',
      ]
    : [
        path.join(rootDir, '.venv', 'bin', 'python'),
        'python3',
        'python',
      ];

  for (const candidate of candidates) {
    if (candidate.includes(path.sep) && !fs.existsSync(candidate)) {
      continue;
    }
    const probe = spawnSync(candidate, ['--version'], { stdio: 'ignore' });
    if (probe.status === 0) {
      return candidate;
    }
  }
  return null;
}

function isPortListening(port, host = '127.0.0.1') {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(400);
    socket.once('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.once('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.once('error', () => {
      socket.destroy();
      resolve(false);
    });
    socket.connect(port, host);
  });
}

async function waitForPort(port, timeoutMs = 8000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isPortListening(port)) {
      return true;
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  return false;
}

async function main() {
  let backendProc = null;
  const backendAlreadyUp = await isPortListening(8000);

  if (!backendAlreadyUp) {
    const pythonBin = resolvePython();
    if (!pythonBin) {
      console.error('[dev] No se encontró Python (.venv ni sistema) para iniciar el backend en :8000.');
      process.exit(1);
    }

    const env = { ...process.env };
    if (!env.ADUANA_MASTER_KEY) {
      const keyFile = path.join(rootDir, 'data', 'dev_master.key');
      if (fs.existsSync(keyFile)) {
        env.ADUANA_MASTER_KEY = fs.readFileSync(keyFile, 'utf8').trim();
      }
    }
    env.ADUANA_RBAC = env.ADUANA_RBAC || '1';
    env.ADUANA_DEMO_MODE = env.ADUANA_DEMO_MODE || '1';
    env.ADUANA_API_TOKEN = env.ADUANA_API_TOKEN || 'aduana-dev-token-local-2026-32bytes';

    console.log('[dev] Iniciando backend soberano Litestar/Granian en http://127.0.0.1:8000 ...');
    backendProc = spawn(
      pythonBin,
      [
        '-m',
        'granian',
        '--interface',
        'asgi',
        '--factory',
        'app.server:create_app',
        '--host',
        '127.0.0.1',
        '--port',
        '8000',
      ],
      {
        cwd: rootDir,
        env,
        stdio: 'inherit',
      }
    );

    backendProc.on('exit', (code) => {
      if (code && code !== 0) {
        console.error(`[dev] Backend en :8000 terminó con código ${code}.`);
      }
    });

    const ready = await waitForPort(8000, 10000);
    if (!ready) {
      console.warn('[dev] Aviso: el backend en :8000 tardó en responder; Vite continuará iniciando.');
    }
  } else {
    console.log('[dev] Backend ya activo en http://127.0.0.1:8000.');
  }

  const viteBin = path.join(rootDir, 'node_modules', 'vite', 'bin', 'vite.js');
  const viteProc = spawn(process.execPath, [viteBin, ...process.argv.slice(2)], {
    cwd: rootDir,
    stdio: 'inherit',
  });

  const shutdown = (signal) => {
    if (viteProc && !viteProc.killed) {
      viteProc.kill(signal);
    }
    if (backendProc && !backendProc.killed) {
      backendProc.kill(signal);
    }
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  viteProc.on('exit', (code) => {
    if (backendProc && !backendProc.killed) {
      backendProc.kill('SIGTERM');
    }
    process.exit(code ?? 0);
  });
}

main().catch((err) => {
  console.error('[dev] Error iniciando entorno de desarrollo:', err);
  process.exit(1);
});
