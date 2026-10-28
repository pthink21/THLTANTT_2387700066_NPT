import {createHash} from 'node:crypto';
import {mkdir, readdir, readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve('build');
const output = path.resolve('reports/build-sha256.json');
const entries = [];

async function visit(dir) {
  for (const entry of await readdir(dir, {withFileTypes: true})) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) await visit(full);
    else if (entry.isFile()) {
      const data = await readFile(full);
      entries.push({path: path.relative(root, full).replaceAll(path.sep, '/'), sha256: createHash('sha256').update(data).digest('hex')});
    }
  }
}

await visit(root);
entries.sort((a, b) => a.path.localeCompare(b.path));
await mkdir(path.dirname(output), {recursive: true});
await writeFile(output, `${JSON.stringify({algorithm: 'SHA-256', files: entries}, null, 2)}\n`);
console.log(`SHA-256 manifest: ${entries.length} files → ${path.relative(process.cwd(), output)}`);
