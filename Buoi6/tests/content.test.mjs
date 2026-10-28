import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile, readdir} from 'node:fs/promises';

const read = (name) => readFile(new URL(`../docs/${name}`, import.meta.url), 'utf8');

test('lab documentation covers the required GitLab workflow', async () => {
  const page = await read('gitlab-cicd.md');
  for (const phrase of ['pipeline đầu tiên', 'Docusaurus', 'GitLab Pages', 'runner']) assert.ok(page.includes(phrase));
});

test('security documentation describes SAST, DAST, SCA and secret scanning', async () => {
  const page = await read('secure-pipeline.md');
  for (const phrase of ['SAST', 'DAST', 'SCA', 'Secret scanning']) assert.ok(page.includes(phrase));
});

test('identity appears in the course introduction', async () => {
  const page = await read('intro.md');
  assert.ok(page.includes('Nguyễn Phúc Thịnh'));
  assert.ok(page.includes('2387700066'));
});

test('evidence gallery has twenty captured CMD screenshots', async () => {
  const images = (await readdir(new URL('../static/evidence/', import.meta.url))).filter((file) => file.endsWith('-cmd.png'));
  const manifest = JSON.parse(await readFile(new URL('../evidence/sha256.json', import.meta.url), 'utf8'));
  assert.equal(images.length, 20);
  assert.equal(manifest.imageCount, 20);
  assert.equal(manifest.images.length, 20);
});
