# MultiAgentProject

This repository is organized for easier fresh installs:

- `Installer/` - small bootstrap folder that is easy to download separately.
- `Source/` - full MAP source tree, including MAP_System, ProjectUpdater,
  CommandCenterUI installer templates, and the full installer.

## Fresh PC Install

Download and run:

```bash
curl -L https://raw.githubusercontent.com/BigCatMellow/MultiAgentProject/main/Installer/install.sh -o install-map.sh
chmod +x install-map.sh
./install-map.sh
```

The bootstrap clones this repository to `~/Projects/MultiAgentProject` by
default, then runs:

```text
Source/MAP-System-Installer.run
```

## Full Source

Browse the project source in:

```text
Source/
```

