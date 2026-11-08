# PyLauncher

A from-scratch Minecraft Java Edition launcher supporting offline accounts.
Written in pure Python. No wrapper libraries, no Mojang launcher code — just
the manifest, the JSON, the HTTP, and the JVM command line.

## Features

- Downloads the client jar, libraries, natives, and assets directly from Mojang
- Verifies every file with SHA1
- Generates the correct offline UUID (`OfflinePlayer:<name>` MD5 scheme)
- Builds the exact JVM and game arguments Mojang expects
- Caches everything — reinstalls are instant
- Config file for username, default version, memory, and Java path

## Requirements

- Python 3.9+
- A JDK compatible with your chosen Minecraft version:
  - 1.17+ → Java 17 or newer
  - 1.13–1.16 → Java 8+
  - 1.12 and older → Java 8

## Install

```bash
git clone https://github.com/faisaljs/PyLauncher.git
cd PyLauncher
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
# See available versions from Mojang
pylauncher available

# Install a version (downloads ~500MB–1GB into ~/.pylauncher)
pylauncher install 1.20.4

# Launch the game (installs automatically if missing)
pylauncher launch 1.20.4 -u YourName

# Or, set defaults and just launch
pylauncher config username YourName
pylauncher config default_version 1.20.4
pylauncher launch
```

### Subcommands

| Command | What it does |
|---|---|
| `pylauncher available` | List all versions Mojang offers |
| `pylauncher install <version>` | Download and verify everything for a version |
| `pylauncher launch [version]` | Start the game (installs if needed) |
| `pylauncher list` | Show installed versions |
| `pylauncher config [key] [value]` | Read or write config |

### Options

- `--dir, -d` — override the game directory (default `~/.pylauncher`)
- `--java, -j` — override the java executable
- `--memory, -m` — max heap in MB
- `--no-install` — fail instead of auto-installing on launch
- `--quiet, -q` — silence install progress

## How it works

See the source. Each module has a single job:

- `manifest.py` — fetch the Mojang version manifest and per-version JSON
- `download.py` — HTTP, SHA1, library / native / asset / client downloaders
- `rules.py` — platform rule evaluation (`windows`/`osx`/`linux`, x86/arm)
- `args.py` — build the classpath, JVM args, game args with placeholder substitution
- `uuid.py` — offline UUID generation
- `launcher.py` — orchestrate install and launch
- `cli.py` — argparse subcommands

## Roadmap

- [x] CLI launcher (v0.1)
- [ ] GUI (v0.2) — Tkinter or PySide6, version picker + progress + log
- [ ] Mod loader support (Fabric, Forge, Quilt)
- [ ] Instance profiles
- [ ] Microsoft account login (online mode)

## License

MIT — see `LICENSE`.