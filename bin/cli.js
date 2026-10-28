#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const SKILL_NAME = 'study-pack-builder';
const COPY_ITEMS = ['SKILL.md', 'scripts', 'references', 'assets', 'examples', 'LICENSE'];

function readVersion() {
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(PACKAGE_ROOT, 'package.json'), 'utf8'));
    return pkg.version || '1.0.0';
  } catch {
    return '1.0.0';
  }
}

function expandHome(value) {
  if (!value) return value;
  if (value === '~') return os.homedir();
  if (value.startsWith('~/')) return path.join(os.homedir(), value.slice(2));
  return value;
}

function usage() {
  console.log(`study-pack-builder ${readVersion()}

Install the Study Pack Builder skill for an agent that reads SKILL.md.

Usage:
  npx github:IvanJairus/study-pack-builder [options]
  npx study-pack-builder [options]        # after npm publish
  node bin/cli.js [options]               # from a clone

Options:
  --project              Install to ./.qoder/skills/${SKILL_NAME}
  --target <path>        Install to a custom directory
  --force                Back up an existing target and replace it
  --dry-run              Print the plan without writing
  --help                 Show this help
  --version              Show the version

Default target:
  ~/.qoder/skills/${SKILL_NAME}

After install:
  1. Run /skills reload in the agent
  2. Invoke /${SKILL_NAME}
`);
}

function parseArgs(argv) {
  const options = { project: false, target: null, force: false, dryRun: false, help: false, version: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--project') options.project = true;
    else if (arg === '--target') {
      options.target = argv[index + 1];
      index += 1;
    } else if (arg.startsWith('--target=')) options.target = arg.slice('--target='.length);
    else if (arg === '--force') options.force = true;
    else if (arg === '--dry-run') options.dryRun = true;
    else if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg === '--version' || arg === '-v') options.version = true;
    else {
      console.error(`Unknown option: ${arg}`);
      options.help = true;
    }
  }
  return options;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    usage();
    return 0;
  }
  if (options.version) {
    console.log(readVersion());
    return 0;
  }

  const defaultTarget = path.join(os.homedir(), '.qoder', 'skills', SKILL_NAME);
  const target = options.target
    ? path.resolve(expandHome(options.target))
    : options.project
      ? path.join(process.cwd(), '.qoder', 'skills', SKILL_NAME)
      : defaultTarget;

  if (!fs.existsSync(path.join(PACKAGE_ROOT, 'SKILL.md'))) {
    console.error(`SKILL.md not found in package root: ${PACKAGE_ROOT}`);
    return 2;
  }

  const items = COPY_ITEMS.filter((item) => fs.existsSync(path.join(PACKAGE_ROOT, item)));
  console.log(`Source: ${PACKAGE_ROOT}`);
  console.log(`Target: ${target}`);
  console.log(`Items:  ${items.join(', ')}`);

  if (options.dryRun) {
    console.log('Dry run: no files written.');
    return 0;
  }

  if (fs.existsSync(target)) {
    if (!options.force) {
      console.error(`Target already exists: ${target}`);
      console.error('Use --force to back it up and replace it, or choose another --target.');
      return 1;
    }
    const backupRoot = path.join(os.homedir(), '.qoder', 'skill-backups');
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backup = path.join(backupRoot, `${SKILL_NAME}-${stamp}`);
    fs.mkdirSync(backupRoot, { recursive: true });
    fs.renameSync(target, backup);
    console.log(`Backup: ${backup}`);
  }

  fs.mkdirSync(target, { recursive: true });
  for (const item of items) {
    fs.cpSync(path.join(PACKAGE_ROOT, item), path.join(target, item), { recursive: true, force: true });
  }

  console.log(`Installed ${SKILL_NAME} to ${target}`);
  console.log('Next: /skills reload, then invoke /study-pack-builder');
  return 0;
}

process.exitCode = main();
