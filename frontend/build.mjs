import { mkdir, copyFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.dirname(fileURLToPath(import.meta.url));
const target = path.join(root, 'dist');
await mkdir(target, { recursive: true });
for (const name of ['index.html', 'style.css', 'app.js']) await copyFile(path.join(root, name), path.join(target, name));
const url = process.env.API_BASE_URL || 'http://localhost:8000';
if (!/^https?:\/\//.test(url)) throw new Error('API_BASE_URL must be an http(s) URL');
await writeFile(path.join(target, 'config.js'), `window.APP_CONFIG = ${JSON.stringify({ apiBaseUrl: url.replace(/\/$/, '') })};\n`);
