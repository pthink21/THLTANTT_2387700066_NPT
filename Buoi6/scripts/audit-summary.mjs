import {spawnSync} from 'node:child_process';
import {mkdir, writeFile} from 'node:fs/promises';

const isWindows = process.platform === 'win32';
const command = isWindows ? (process.env.ComSpec || 'cmd.exe') : 'npm';
const args = isWindows
  ? ['/d', '/s', '/c', 'npm.cmd audit --json --audit-level=high']
  : ['audit', '--json', '--audit-level=high'];
const result = spawnSync(command, args, {
  encoding: 'utf8',
  shell: false,
  maxBuffer: 16 * 1024 * 1024,
});

let report;
try {
  report = JSON.parse(result.stdout);
} catch {
  console.error('npm audit did not return a valid JSON report.');
  if (result.stderr) console.error(result.stderr.trim());
  process.exit(result.status || 1);
}

await mkdir('evidence', {recursive: true});
await writeFile('evidence/npm-audit.json', `${JSON.stringify(report, null, 2)}\n`);
const counts = report.metadata?.vulnerabilities ?? {};
console.log('Dependency audit (npm audit --audit-level=high)');
console.log(`Critical: ${counts.critical ?? 0} | High: ${counts.high ?? 0} | Moderate: ${counts.moderate ?? 0} | Low: ${counts.low ?? 0}`);
console.log('Detailed JSON: evidence/npm-audit.json');
if (result.stderr?.trim()) console.log(result.stderr.trim());

if (result.status !== 0) {
  console.error(`npm audit gate failed (exit ${result.status}).`);
  process.exit(result.status || 1);
}
