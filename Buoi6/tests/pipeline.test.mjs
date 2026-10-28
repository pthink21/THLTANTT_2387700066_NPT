import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import YAML from 'yaml';

const config = YAML.parse(await readFile(new URL('../.gitlab-ci.yml', import.meta.url), 'utf8'));

test('GitLab CI stages keep security before build and deploy', () => {
  assert.deepEqual(config.stages, ['test', 'security', 'build', 'deploy']);
});

test('pipeline has the tutorial gates and Pages job', () => {
  for (const name of ['unit-tests', 'security-check', 'dependency-audit', 'semgrep', 'secret-scan', 'build-job', 'pages']) {
    assert.ok(config[name], `${name} job should be present`);
  }
});

test('Pages deploy is limited to the default branch', () => {
  assert.equal(config.pages.rules[0].if, '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH');
  assert.deepEqual(config['build-job'].artifacts.paths, ['Buoi6/build/', 'Buoi6/reports/build-sha256.json']);
  assert.deepEqual(config.pages.dependencies, ['build-job']);
});

test('GitHub Actions mirror runs the Buoi6 verification workflow', async () => {
  const workflow = await readFile(new URL('../../.github/workflows/buoi6.yml', import.meta.url), 'utf8');
  assert.ok(workflow.includes('working-directory: Buoi6'));
  for (const command of ['npm test', 'npm run security', 'npm run audit', 'npm run build', 'npm run checksums']) {
    assert.ok(workflow.includes(`run: ${command}`));
  }
});
