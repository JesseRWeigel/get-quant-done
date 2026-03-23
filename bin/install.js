#!/usr/bin/env node
/**
 * Get Quant Done installer
 *
 * Adapted from get-physics-done's installer pattern.
 * Sets up a managed Python venv, installs the package, and registers
 * MCP servers + agents + commands with Claude Code.
 *
 * Usage:
 *   npx get-quant-done                  # Interactive
 *   npx get-quant-done --local          # Install into current project
 *   npx get-quant-done --global         # Install globally
 *   npx get-quant-done --uninstall      # Remove
 */

const { execFileSync, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const readline = require("readline");

// ── Brand Config ──────────────────────────────────────────────────────

const BRAND = {
  name: "get-quant-done",
  displayName: "Get Quant Done",
  prefix: "gqd",
  pyModule: "gqd",
  homeDir: ".gqd",
  homeDirEnv: "GQD_HOME",
  description: "AI copilot for autonomous quantitative finance research",
  repo: "https://github.com/JesseRWeigel/get-quant-done",
};

// ── Python Detection ──────────────────────────────────────────────────

function findPython() {
  const candidates = ["python3.13", "python3.12", "python3.11", "python3", "python"];
  for (const cmd of candidates) {
    try {
      const result = spawnSync(cmd, ["--version"], { encoding: "utf-8" });
      if (result.status !== 0) continue;
      const version = (result.stdout || result.stderr).trim();
      const match = version.match(/Python (\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);
        if (major === 3 && minor >= 11) {
          const venvCheck = spawnSync(cmd, ["-m", "venv", "--help"], { stdio: "pipe" });
          if (venvCheck.status === 0) return cmd;
        }
      }
    } catch {
      continue;
    }
  }
  return null;
}

// ── Managed Venv ──────────────────────────────────────────────────────

function getHome() {
  return process.env[BRAND.homeDirEnv] || path.join(os.homedir(), BRAND.homeDir);
}

function ensureVenv(basePython) {
  const home = getHome();
  const venvDir = path.join(home, "venv");
  const python = path.join(venvDir, "bin", "python");

  if (!fs.existsSync(python)) {
    console.log(`Creating managed Python environment at ${venvDir}...`);
    fs.mkdirSync(home, { recursive: true });
    execFileSync(basePython, ["-m", "venv", venvDir], { stdio: "inherit" });
    execFileSync(python, ["-m", "ensurepip", "--upgrade"], { stdio: "pipe" });
  }

  return { home, venvDir, python };
}

// ── Package Installation ──────────────────────────────────────────────

function installPackage(python) {
  console.log("Installing Python package...");

  // Try installing from the local source directory first (for dev / npx from repo)
  const localSrc = path.join(__dirname, "..");
  const localPyproject = path.join(localSrc, "pyproject.toml");
  if (fs.existsSync(localPyproject)) {
    console.log("  Installing from local source...");
    const result = spawnSync(python, ["-m", "pip", "install", "--quiet", "-e", localSrc], {
      stdio: "inherit",
      timeout: 120000,
    });
    if (result.status === 0) return true;
  }

  // Try GitHub source archive
  const sources = [
    `git+${BRAND.repo}.git@master`,
    `${BRAND.repo}/archive/refs/heads/master.tar.gz`,
  ];

  for (const source of sources) {
    console.log(`  Trying ${source}...`);
    const result = spawnSync(python, ["-m", "pip", "install", "--upgrade", "--quiet", source], {
      stdio: "inherit",
      timeout: 120000,
    });
    if (result.status === 0) return true;
  }

  console.error("Failed to install Python package. Try manually:");
  console.error(`  ${python} -m pip install git+${BRAND.repo}.git`);
  return false;
}

// ── Claude Code Registration ──────────────────────────────────────────

function registerWithClaudeCode(env, scope) {
  const configDir = scope === "global"
    ? path.join(os.homedir(), ".claude")
    : path.join(process.cwd(), ".claude");

  const mcpConfigPath = scope === "global"
    ? path.join(os.homedir(), ".claude.json")
    : path.join(process.cwd(), ".mcp.json");

  // Ensure config directories
  fs.mkdirSync(configDir, { recursive: true });
  fs.mkdirSync(path.join(configDir, "commands", BRAND.prefix), { recursive: true });
  fs.mkdirSync(path.join(configDir, "agents"), { recursive: true });

  // ── Register MCP servers ──
  let mcpConfig = {};
  if (fs.existsSync(mcpConfigPath)) {
    try {
      mcpConfig = JSON.parse(fs.readFileSync(mcpConfigPath, "utf-8"));
    } catch {}
  }
  if (!mcpConfig.mcpServers) mcpConfig.mcpServers = {};

  const servers = {
    [`${BRAND.prefix}-state`]: `${BRAND.pyModule}.mcp.state_server`,
    [`${BRAND.prefix}-conventions`]: `${BRAND.pyModule}.mcp.conventions_server`,
    [`${BRAND.prefix}-protocols`]: `${BRAND.pyModule}.mcp.protocols_server`,
    [`${BRAND.prefix}-verification`]: `${BRAND.pyModule}.mcp.verification_server`,
    [`${BRAND.prefix}-errors`]: `${BRAND.pyModule}.mcp.errors_server`,
    [`${BRAND.prefix}-patterns`]: `${BRAND.pyModule}.mcp.patterns_server`,
  };

  for (const [key, module] of Object.entries(servers)) {
    mcpConfig.mcpServers[key] = {
      command: env.python,
      args: ["-m", module],
      env: { LOG_LEVEL: "WARNING" },
    };
  }

  fs.writeFileSync(mcpConfigPath, JSON.stringify(mcpConfig, null, 2) + "\n");
  console.log(`Registered ${Object.keys(servers).length} MCP servers in ${mcpConfigPath}`);

  // ── Install agents ──
  const agentsDir = path.join(configDir, "agents");
  const srcAgentsDir = findSrcDir(env, "agents");
  if (srcAgentsDir) {
    const agents = fs.readdirSync(srcAgentsDir).filter(f => f.endsWith(".md"));
    for (const agent of agents) {
      let content = fs.readFileSync(path.join(srcAgentsDir, agent), "utf-8");
      content = replacePlaceholders(content, env, configDir);
      fs.writeFileSync(path.join(agentsDir, agent), content);
    }
    console.log(`Installed ${agents.length} agents`);
  }

  // ── Install commands ──
  const commandsDir = path.join(configDir, "commands", BRAND.prefix);
  const srcCommandsDir = findSrcDir(env, "commands");
  if (srcCommandsDir) {
    const commands = fs.readdirSync(srcCommandsDir).filter(f => f.endsWith(".md"));
    for (const cmd of commands) {
      let content = fs.readFileSync(path.join(srcCommandsDir, cmd), "utf-8");
      content = replacePlaceholders(content, env, configDir);
      fs.writeFileSync(path.join(commandsDir, cmd), content);
    }
    console.log(`Installed ${commands.length} commands as /${BRAND.prefix}:<name>`);
  }

  // ── Install reference specs ──
  const specsDestDir = path.join(configDir, BRAND.name);
  const srcSpecsDir = findSrcDir(env, "specs");
  if (srcSpecsDir) {
    copyDirRecursive(srcSpecsDir, specsDestDir);
    console.log(`Installed reference specs`);
  }

  // ── Install hooks (statusline) ──
  const hooksDir = path.join(configDir, "hooks");
  fs.mkdirSync(hooksDir, { recursive: true });
  const srcHooksDir = findSrcDir(env, "hooks");
  if (srcHooksDir) {
    const hooks = fs.readdirSync(srcHooksDir).filter(f => f.endsWith(".py"));
    for (const hook of hooks) {
      fs.copyFileSync(path.join(srcHooksDir, hook), path.join(hooksDir, hook));
    }
    console.log(`Installed ${hooks.length} hook(s)`);
  }

  // ── Configure statusline in settings.json ──
  const settingsPath = path.join(configDir, "settings.json");
  let settings = {};
  if (fs.existsSync(settingsPath)) {
    try { settings = JSON.parse(fs.readFileSync(settingsPath, "utf-8")); } catch {}
  }
  const statuslineScript = path.join(hooksDir, "statusline.py");
  if (fs.existsSync(statuslineScript)) {
    settings.statusLine = settings.statusLine || {};
    settings.statusLine.command = `${env.python} ${statuslineScript}`;
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n");
    console.log(`Configured statusline hook`);
  }

  // ── Write manifest ──
  const manifest = {
    version: require("../package.json").version,
    brand: BRAND.name,
    prefix: BRAND.prefix,
    installScope: scope,
    python: env.python,
    installedAt: new Date().toISOString(),
  };
  fs.writeFileSync(
    path.join(configDir, `${BRAND.prefix}-manifest.json`),
    JSON.stringify(manifest, null, 2) + "\n"
  );

  console.log(`\n✓ ${BRAND.displayName} installed successfully!`);
  console.log(`  Run /${BRAND.prefix}:new-project to start a research project.\n`);
}

// ── Uninstall ─────────────────────────────────────────────────────────

function uninstall(scope) {
  const configDir = scope === "global"
    ? path.join(os.homedir(), ".claude")
    : path.join(process.cwd(), ".claude");

  const mcpConfigPath = scope === "global"
    ? path.join(os.homedir(), ".claude.json")
    : path.join(process.cwd(), ".mcp.json");

  // Remove MCP servers
  if (fs.existsSync(mcpConfigPath)) {
    try {
      const config = JSON.parse(fs.readFileSync(mcpConfigPath, "utf-8"));
      if (config.mcpServers) {
        for (const key of Object.keys(config.mcpServers)) {
          if (key.startsWith(`${BRAND.prefix}-`)) {
            delete config.mcpServers[key];
          }
        }
        fs.writeFileSync(mcpConfigPath, JSON.stringify(config, null, 2) + "\n");
      }
    } catch {}
  }

  // Remove agents
  const agentsDir = path.join(configDir, "agents");
  if (fs.existsSync(agentsDir)) {
    for (const f of fs.readdirSync(agentsDir)) {
      if (f.startsWith(`${BRAND.prefix}-`)) {
        fs.unlinkSync(path.join(agentsDir, f));
      }
    }
  }

  // Remove commands, specs, manifest
  for (const dir of [
    path.join(configDir, "commands", BRAND.prefix),
    path.join(configDir, BRAND.name),
  ]) {
    if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true });
  }

  const manifestPath = path.join(configDir, `${BRAND.prefix}-manifest.json`);
  if (fs.existsSync(manifestPath)) fs.unlinkSync(manifestPath);

  console.log(`✓ ${BRAND.displayName} uninstalled.`);
}

// ── Helpers ───────────────────────────────────────────────────────────

function findSrcDir(env, subdir) {
  // Try installed package location
  try {
    const result = spawnSync(env.python, [
      "-c",
      `import ${BRAND.pyModule}; import os; print(os.path.dirname(${BRAND.pyModule}.__file__))`,
    ], { encoding: "utf-8" });
    if (result.status === 0) {
      const dir = path.join(result.stdout.trim(), subdir);
      if (fs.existsSync(dir)) return dir;
    }
  } catch {}

  // Fallback: local repo checkout
  const localDir = path.join(__dirname, "..", "src", BRAND.pyModule, subdir);
  return fs.existsSync(localDir) ? localDir : null;
}

function replacePlaceholders(content, env, configDir) {
  const prefix = BRAND.prefix.toUpperCase();
  return content
    .replace(new RegExp(`\\{${prefix}_INSTALL_DIR\\}`, "g"), path.join(configDir, BRAND.name))
    .replace(new RegExp(`\\{${prefix}_AGENTS_DIR\\}`, "g"), path.join(configDir, "agents"))
    .replace(new RegExp(`\\{${prefix}_CONFIG_DIR\\}`, "g"), configDir)
    .replace(new RegExp(`\\{${prefix}_PYTHON\\}`, "g"), env.python);
}

function copyDirRecursive(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function prompt(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

// ── Main ──────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  console.log(`\n${BRAND.displayName} — ${BRAND.description}\n`);

  // Handle uninstall
  if (args.includes("--uninstall") || args.includes("uninstall")) {
    const scope = args.includes("--global") || args.includes("-g") ? "global" : "local";
    uninstall(scope);
    return;
  }

  // Determine scope
  let scope;
  if (args.includes("--global") || args.includes("-g")) {
    scope = "global";
  } else if (args.includes("--local") || args.includes("-l")) {
    scope = "local";
  } else if (process.stdin.isTTY) {
    const answer = await prompt(
      "Install scope:\n  [1] Local (this project)\n  [2] Global (~/.claude)\n\nChoice [1]: "
    );
    scope = answer === "2" ? "global" : "local";
  } else {
    scope = "local";
  }

  // Find Python
  const basePython = findPython();
  if (!basePython) {
    console.error("Error: Python 3.11+ with venv module required.");
    console.error("Install: https://www.python.org/downloads/");
    process.exit(1);
  }
  console.log(`Using Python: ${basePython}`);

  // Setup venv
  const env = ensureVenv(basePython);
  console.log(`Managed environment: ${env.venvDir}`);

  // Install Python package
  installPackage(env.python);

  // Register with Claude Code
  registerWithClaudeCode(env, scope);
}

main().catch(err => {
  console.error("Installation failed:", err.message);
  process.exit(1);
});
