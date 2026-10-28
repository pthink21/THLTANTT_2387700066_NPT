import {readFile, readdir} from 'node:fs/promises';
import path from 'node:path';
import YAML from 'yaml';

const mode = process.argv[2];
const pkg = JSON.parse(await readFile('package.json', 'utf8'));
const pipelineText = await readFile('.gitlab-ci.yml', 'utf8');
const pipeline = YAML.parse(pipelineText);

switch (mode) {
  case 'package':
    console.log(`Project: ${pkg.name}`);
    console.log(`Required Node.js: ${pkg.engines.node}`);
    console.log('Scripts:', Object.keys(pkg.scripts).join(', '));
    break;
  case 'gitlab-yaml':
    console.log('GitLab CI YAML: valid');
    console.log(`Stages: ${pipeline.stages.join(' > ')}`);
    break;
  case 'build-files': {
    let files = 0;
    async function walk(dir) {
      for (const entry of await readdir(dir, {withFileTypes: true})) {
        if (entry.isDirectory()) await walk(path.join(dir, entry.name));
        else files++;
      }
    }
    await walk('build');
    console.log(`Static build files: ${files}`);
    console.log(`Homepage generated: ${(await readdir('build')).includes('index.html')}`);
    break;
  }
  case 'manifest': {
    const manifest = JSON.parse(await readFile('reports/build-sha256.json', 'utf8'));
    console.log(`Algorithm: ${manifest.algorithm}`);
    console.log(`Hashed files: ${manifest.files.length}`);
    for (const item of manifest.files.slice(0, 3)) console.log(`${item.sha256}  ${item.path}`);
    break;
  }
  case 'http': {
    const url = 'http://127.0.0.1:3000/THLTANTT_2387700066_NPT/';
    const response = await fetch(url);
    const html = await response.text();
    console.log(`Preview URL: ${url}`);
    console.log(`HTTP status: ${response.status}`);
    console.log(`Document title present: ${/<title(?:\s|>)/i.test(html)}`);
    if (!response.ok) process.exitCode = 1;
    break;
  }
  case 'deploy-rule':
    console.log(`Pages stage: ${pipeline.pages.stage}`);
    console.log(`Deploy condition: ${pipeline.pages.rules[0].if}`);
    console.log(`Artifact source: ${pipeline['build-job'].artifacts.paths[0]}`);
    break;
  case 'responsive': {
    const css = await readFile('src/pages/index.module.css', 'utf8');
    const breakpoints = [...css.matchAll(/@media\s*\(([^)]+)\)/g)].map((match) => match[1]);
    console.log('Responsive CSS breakpoints:');
    for (const breakpoint of breakpoints) console.log(`- ${breakpoint}`);
    break;
  }
  case 'docs': {
    const files = (await readdir('docs')).filter((file) => file.endsWith('.md')).sort();
    console.log(`Documentation pages (${files.length}):`);
    for (const file of files) console.log(`- ${file}`);
    break;
  }
  default:
    console.error('Usage: node scripts/evidence-check.mjs <package|gitlab-yaml|build-files|http|manifest|deploy-rule|responsive|docs>');
    process.exitCode = 2;
}
