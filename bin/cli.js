#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const SKILL_NAME = 'study-pack-builder';
const COPY_ITEMS = ['SKILL.md', 'scripts', 'references', 'assets', 'examples', 'LICENSE'];

const TARGETS = [
  { id: 'qoder', label: 'Qoder', config: '.qoder', path: '.qoder/skills/' + SKILL_NAME },
  { id: 'claude', label: 'Claude Code', config: '.claude', path: '.claude/skills/' + SKILL_NAME },
  { id: 'cursor', label: 'Cursor', config: '.cursor', path: '.cursor/skills/' + SKILL_NAME },
  { id: 'antigravity', label: 'Antigravity', config: '.gemini/antigravity', path: '.gemini/antigravity/skills/' + SKILL_NAME },
  { id: 'codex', label: 'Codex', config: '.codex', path: '.codex/skills/' + SKILL_NAME }
];

const UNSUPPORTED = [
  {
    id: 'workbuddy',
    label: 'WorkBuddy AI',
    paths: [
      '/Applications/WorkBuddy AI.app',
      path.join(os.homedir(), 'Library', 'Application Support', 'WorkBuddy AI')
    ],
    note: 'app found, no supported skills folder; use manual instructions'
  }
];

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

function targetPath(target) {
  return path.join(os.homedir(), target.path);
}

function isDetected(target) {
  return fs.existsSync(path.join(os.homedir(), target.config));
}

function projectTargetPath(target) {
  return path.join(process.cwd(), target.config, 'skills', SKILL_NAME);
}

function isProjectDetected(target) {
  return fs.existsSync(path.join(process.cwd(), target.config));
}

function usage() {
  console.log(`study-pack-builder ${readVersion()}

Install the Study Pack Builder skill into every detected agent, or into a chosen target.

Usage:
  npx github:IvanJairus/study-pack-builder [options]
  npx study-pack-builder [options]        # after npm publish
  node bin/cli.js [options]               # from a clone

Options:
  --list                 Show detected agents and paths, then exit
  --all                  Install to every supported agent path, even if not detected
  --agent <ids>          Install only to comma-separated agent ids
  --project              Install to detected project-level config folders
  --target <path>        Install to one custom directory
  --force                Back up existing installs and replace them
  --dry-run              Print the plan without writing
  --help                 Show this help
  --version              Show the version

Supported ids:
  qoder, claude, cursor, antigravity, codex

Default:
  Detect supported agents and install to all detected user-level paths.
  If none are detected, use --all or --target.

After install:
  1. Reload skills in each agent
  2. Invoke /${SKILL_NAME}
`);
}

function parseArgs(argv) {
  const options = {
    list: false,
    all: false,
    agents: [],
    project: false,
    target: null,
    force: false,
    dryRun: false,
    help: false,
    version: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--list') options.list = true;
    else if (arg === '--all') options.all = true;
    else if (arg === '--project') options.project = true;
    else if (arg === '--force') options.force = true;
    else if (arg === '--dry-run') options.dryRun = true;
    else if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg === '--version' || arg === '-v') options.version = true;
    else if (arg === '--agent') {
      options.agents.push(...String(argv[index + 1] || '').split(',').map((value) => value.trim()).filter(Boolean));
      index += 1;
    } else if (arg.startsWith('--agent=')) {
      options.agents.push(...arg.slice('--agent='.length).split(',').map((value) => value.trim()).filter(Boolean));
    } else if (arg === '--target') {
      options.target = argv[index + 1];
      index += 1;
    } else if (arg.startsWith('--target=')) {
      options.target = arg.slice('--target='.length);
    } else {
      console.error(`Unknown option: ${arg}`);
      options.help = true;
    }
  }
  return options;
}

function printList() {
  console.log('User-level agents:');
  for (const target of TARGETS) {
    const detected = isDetected(target);
    console.log(`  ${detected ? '[detected]' : '[not found]'} ${target.id.padEnd(12)} ${targetPath(target)}`);
  }
  console.log('');
  console.log('Project-level configs in the current directory:');
  const projectHits = TARGETS.filter(isProjectDetected);
  if (!projectHits.length) {
    console.log('  [not found] no .qoder, .claude, .cursor, .gemini/antigravity, or .codex');
  } else {
    for (const target of projectHits) {
      console.log(`  [detected] ${target.id.padEnd(12)} ${projectTargetPath(target)}`);
    }
  }
  console.log('');
  for (const item of UNSUPPORTED) {
    if (item.paths.some((candidate) => fs.existsSync(candidate))) {
      console.log(`  [manual]   ${item.id.padEnd(12)} ${item.note}`);
    }
  }
}

function ensureSource() {
  if (!fs.existsSync(path.join(PACKAGE_ROOT, 'SKILL.md'))) {
    console.error(`SKILL.md not found in package root: ${PACKAGE_ROOT}`);
    return false;
  }
  return true;
}

function copySkill(target) {
  fs.mkdirSync(target, { recursive: true });
  for (const item of COPY_ITEMS) {
    const source = path.join(PACKAGE_ROOT, item);
    if (!fs.existsSync(source)) continue;
    fs.cpSync(source, path.join(target, item), { recursive: true, force: true });
  }
}

function backupTarget(target, id) {
  const backupRoot = path.join(os.homedir(), '.study-pack-builder', 'backups');
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backup = path.join(backupRoot, `${id}-${stamp}`);
  fs.mkdirSync(backupRoot, { recursive: true });
  fs.renameSync(target, backup);
  return backup;
}

function installOne(target, options) {
  const exists = fs.existsSync(target);
  if (exists && !options.force) {
    return { status: 'skipped', target };
  }
  if (options.dryRun) {
    return { status: exists ? 'would-update' : 'would-install', target };
  }
  let backup = null;
  if (exists) backup = backupTarget(target, options.id);
  copySkill(target);
  return { status: exists ? 'updated' : 'installed', target, backup };
}

function selectedTargets(options) {
  if (options.target) {
    return [{ id: 'custom', label: 'Custom', path: path.resolve(expandHome(options.target)) }];
  }

  if (options.project) {
    const detected = TARGETS.filter(isProjectDetected);
    if (detected.length) {
      return detected.map((target) => ({ ...target, path: projectTargetPath(target), project: true }));
    }
    return [{ ...TARGETS[0], path: path.join(process.cwd(), '.qoder', 'skills', SKILL_NAME), project: true, fallback: true }];
  }

  let candidates;
  if (options.agents.length) {
    const ids = options.agents.map((value) => value.toLowerCase());
    const unknown = ids.filter((id) => !TARGETS.some((target) => target.id === id));
    if (unknown.length) {
      console.error(`Unknown agent id: ${unknown.join(', ')}`);
      console.error(`Supported ids: ${TARGETS.map((target) => target.id).join(', ')}`);
      return null;
    }
    candidates = TARGETS.filter((target) => ids.includes(target.id));
  } else if (options.all) {
    candidates = TARGETS.slice();
  } else {
    candidates = TARGETS.filter(isDetected);
    if (!candidates.length) {
      console.error('No supported agent config detected.');
      console.error('Use --all to install everywhere, --agent <ids>, or --target <path>.');
      return null;
    }
  }

  return candidates.map((target) => ({ ...target, path: targetPath(target) }));
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
  if (options.list) {
    printList();
    return 0;
  }
  if (!ensureSource()) return 2;

  const targets = selectedTargets(options);
  if (!targets) return 1;

  console.log(`Source: ${PACKAGE_ROOT}`);
  console.log(`Targets: ${targets.map((target) => target.id).join(', ')}`);
  if (options.dryRun) console.log('Dry run: no files written.');

  const results = [];
  for (const target of targets) {
    const result = installOne(target.path, { ...options, id: target.id });
    results.push({ ...result, id: target.id, label: target.label });
    const suffix = result.status === 'skipped' ? ' (exists; use --force to update)' : '';
    console.log(`  ${result.status.padEnd(14)} ${target.label.padEnd(12)} ${result.target}${suffix}`);
    if (result.backup) console.log(`  backup         ${result.backup}`);
  }

  const installed = results.filter((result) => result.status === 'installed' || result.status === 'updated');
  const skipped = results.filter((result) => result.status === 'skipped');
  if (installed.length) console.log(`\nInstalled: ${installed.map((result) => result.id).join(', ')}`);
  if (skipped.length) console.log(`Skipped:   ${skipped.map((result) => result.id).join(', ')}`);
  if (!installed.length && !skipped.length) return 1;

  console.log(`\nNext: reload skills in each agent, then invoke /${SKILL_NAME}`);
  return 0;
}

process.exitCode = main();
