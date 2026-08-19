#!/usr/bin/env node
'use strict';

const path = require('path');
const fs = require('fs');

const { isExcluded, isSecretFile, hasSpaces, EXCLUSIONS_PROFILE, matchesAnyPattern } = require('../lib/exclusions');
const fp = require('../lib/fingerprint');
const { generateInventory, SCOPE_DIRS } = require('../lib/inventory');
const { generateClassesXml } = require('../lib/classesXml');
const { xsdValidator } = require('../lib/index');
const { generateBundle } = require('../lib/repomixBundle');

const REPO_ROOT = path.join(__dirname, '..', '..', '..', '..');

const USAGE = `
ffai-structure v1.0.0 — FitFlow AI structural context discovery

USAGE:
  ffai structure dirs --scope <backend|frontend|total> [--out <dir>]
      Generate directory inventory.

  ffai structure classes --scope <backend|frontend|total> [--out <dir>]
      Generate estructura_de_clases_<fecha>.xml and validate against XSD.

  ffai snapshot --scope <backend|frontend|total> --task <TASK_ID> [--out <dir>]
      Generate Repomix bundle + INDEX_RUN manifest.

  ffai check --path <file>
      Check exclusion status of a path (secret, excluded, has-spaces).

  ffai fingerprint [--repo <dir>]
      Print baseline revision + working tree fingerprint.

EXIT CODES:
  0  success / schema valid
  2  input/config invalid
  3  artifact stale
  4  dependency unavailable
  5  parsing/ingestion/validation failure
  6  blocked by policy
`;

function usageAndExit(code) {
  process.stderr.write(USAGE);
  process.exit(code || 2);
}

function parseArgs(argv) {
  const args = [];
  const opts = {};
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg.startsWith('--')) {
      const key = arg.slice(2);
      if (i + 1 < argv.length && !argv[i + 1].startsWith('--')) {
        opts[key] = argv[i + 1];
        i++;
      } else {
        opts[key] = true;
      }
    } else {
      args.push(arg);
    }
  }
  return { args, opts };
}

function main() {
  const { args, opts } = parseArgs(process.argv);
  const [cmd, subcmd] = args;

  if (!cmd) usageAndExit(0);

  switch (cmd) {
    case 'structure':
      handleStructure([subcmd, ...args.slice(1)], opts);
      break;
    case 'snapshot':
      handleSnapshot(opts);
      break;
    case 'check':
      handleCheck(opts);
      break;
    case 'fingerprint':
      handleFingerprint(opts);
      break;
    case '--help':
    case '-h':
    case 'help':
      usageAndExit(0);
      break;
    default:
      usageAndExit(2);
  }
}

function handleStructure(args, opts) {
  const subcmd = args[0];
  const scope = opts.scope;
  if (!scope || !SCOPE_DIRS[scope]) {
    process.stderr.write('Error: --scope must be one of backend, frontend, total\n');
    process.exit(2);
  }

  const outDir = opts.out || (
    subcmd === 'dirs'
      ? path.join(REPO_ROOT, 'docs', 'directorios', 'Estructura directorios')
      : path.join(REPO_ROOT, 'docs', 'directorios', 'Estructura de Clases')
  );

  if (subcmd === 'dirs') {
    const result = generateInventory(scope, REPO_ROOT, outDir);
    const stdout = JSON.stringify(result, null, 2);
    process.stdout.write(stdout + '\n');
    process.exit(0);
  }

  if (subcmd === 'classes') {
    const result = generateClassesXml(scope, REPO_ROOT, outDir);
    if (!result.xsdValid) {
      process.stderr.write('XSD validation failed:\n');
      for (const e of result.xsdErrors) process.stderr.write('  - ' + e + '\n');
      process.exit(5);
    }
    const stdout = JSON.stringify(result, null, 2);
    process.stdout.write(stdout + '\n');
    process.exit(0);
  }

  process.stderr.write('Error: unknown structure subcommand: ' + subcmd + '\n');
  process.exit(2);
}

function handleSnapshot(opts) {
  const scope = opts.scope;
  const taskName = opts.task;
  if (!scope || !SCOPE_DIRS[scope]) {
    process.stderr.write('Error: --scope must be one of backend, frontend, total\n');
    process.exit(2);
  }
  if (!taskName) {
    process.stderr.write('Error: --task is required\n');
    process.exit(2);
  }

  const outDir = opts.out;
  const result = generateBundle(scope, taskName, REPO_ROOT, outDir);
  const stdout = JSON.stringify(result, null, 2);
  process.stdout.write(stdout + '\n');
  process.exit(result.bundleGenerated ? 0 : 4);
}

function handleCheck(opts) {
  const relPath = opts.path;
  if (!relPath) {
    process.stderr.write('Error: --path is required\n');
    process.exit(2);
  }
  const norm = path.normalize(relPath).replace(/\\/g, '/');
  const excluded = isExcluded(norm) || isExcluded(norm + '/', {});
  const secret = isSecretFile(norm);
  const spaces = hasSpaces(norm);
  const result = { path: relPath, excluded, secret, hasSpaces: spaces };
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  process.exit(0);
}

function handleFingerprint(opts) {
  const repoRoot = opts.repo || REPO_ROOT;
  const result = fp.computeWorkingTreeFingerprint(repoRoot);
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  process.exit(0);
}

main();
