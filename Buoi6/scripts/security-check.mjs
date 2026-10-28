import {createHash} from 'node:crypto';
import {readFile, readdir} from 'node:fs/promises';
import path from 'node:path';
import YAML from 'yaml';

const root = process.cwd();
const pipelinePath = path.join(root, '.gitlab-ci.yml');
const pipelineText = await readFile(pipelinePath, 'utf8');
const pipeline = YAML.parse(pipelineText, {uniqueKeys: true});
const requiredStages = ['test', 'security', 'build', 'deploy'];
const problems = [];

if (JSON.stringify(pipeline.stages) !== JSON.stringify(requiredStages)) {
  problems.push(`Pipeline stages must be ordered: ${requiredStages.join(' → ')}`);
}
for (const jobName of ['unit-tests', 'security-check', 'dependency-audit', 'semgrep', 'secret-scan', 'build-job', 'pages']) {
  if (!pipeline[jobName]) problems.push(`Required CI job is missing: ${jobName}`);
}
if (pipeline.pages?.rules?.[0]?.if !== '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH') {
  problems.push('Pages deployment must be restricted to the default branch.');
}
if (pipeline.pages?.needs || pipeline.pages?.allow_failure === true) {
  problems.push('Pages must wait for the build and security stages to succeed.');
}
if (/\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_-]{20,})\b/.test(pipelineText)) {
  problems.push('A token-like credential was found in CI configuration.');
}

const docs = await readdir(path.join(root, 'docs'));
for (const expected of ['intro.md', 'secure-pipeline.md', 'gitlab-cicd.md', 'complex-pipeline.md', 'results.md', 'references.md']) {
  if (!docs.includes(expected)) problems.push(`Documentation page is missing: docs/${expected}`);
}

try {
  const manifest = JSON.parse(await readFile(path.join(root, 'evidence/sha256.json'), 'utf8'));
  const images = (await readdir(path.join(root, 'static/evidence'))).filter((file) => file.endsWith('-cmd.png')).sort();
  if (manifest.algorithm !== 'SHA-256' || manifest.imageCount !== 20 || images.length !== 20 || manifest.images.length !== 20) {
    problems.push(`Evidence must contain exactly 20 manifested CMD screenshots (found ${images.length}).`);
  }
  for (const image of images) {
    const data = await readFile(path.join(root, 'static/evidence', image));
    const actual = createHash('sha256').update(data).digest('hex');
    const recorded = manifest.images.find((item) => item.file === image)?.sha256;
    const logName = image.replace('.png', '.txt');
    const log = await readFile(path.join(root, 'evidence/logs', logName), 'utf8');
    if (actual !== recorded) problems.push(`Screenshot hash does not match evidence manifest: ${image}`);
    if (!log.includes('Exit code: 0')) problems.push(`Evidence command did not report success: ${logName}`);
  }
} catch (error) {
  problems.push(`Screenshot evidence is incomplete: ${error.message}`);
}

if (problems.length) {
  console.error('Security policy: FAIL');
  for (const item of problems) console.error(`- ${item}`);
  process.exitCode = 1;
} else {
  console.log('Security policy: PASS');
  console.log(`- ${requiredStages.length} ordered stages`);
  console.log('- 7 required jobs present');
  console.log('- Pages restricted to the default branch');
  console.log(`- ${docs.length} documentation pages present`);
  console.log('- 20 CMD screenshots and logs match the SHA-256 manifest');
  console.log('- No token pattern found in pipeline config');
}
