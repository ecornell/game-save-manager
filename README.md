# 🎮 Save Game Backup Manager

A comprehensive command-line tool for backing up, restoring, and managing game save files. Keep your precious game progress safe with automated backups, easy restoration, and organized storage.

## ✨ Features

- **🎮 Multi-Game Support**: Configure and manage multiple games with individual settings
- **💾 Automated Backups**: Create timestamped backups with optional descriptions
- **🔄 Easy Restoration**: Restore any backup with a simple menu interface
- **🧹 Intelligent Cleanup**: Automatically manage backup storage with configurable limits
- **📊 Progress Tracking**: Visual progress bars for backup and restore operations
- **🎨 Colorful Interface**: Beautiful terminal output with emojis and colors
- **⚙️ Flexible Configuration**: JSON-based configuration with hot-reloading
- **🛡️ Safety Features**: Pre-restore safety backups and error handling
- **📝 Backup Descriptions**: Add descriptive notes to your backups
- **📊 Size Reporting**: Track backup sizes and save directory information

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- UV package manager (recommended) or standard Python

### Installation

1. Clone or download this repository
2. Ensure you have UV installed, or use standard Python
3. Run the backup tool:

```bash
# Using the provided batch file (Windows)
backup.bat

# Or directly with UV
uv run backup.py

# Or with standard Python
python backup.py
```

### First Run Setup

On first run, the tool will create a default configuration file (`games_config.json`) that you can customize for your games.

## 📖 Usage

### Interactive Mode (Recommended)

Simply run the tool without arguments for the full interactive experience:

```bash
backup.bat
```

This provides a user-friendly menu interface for all operations.

### Command Line Usage

```bash
# Quick backup of configured game
uv run backup.py --game grim_dawn --backup

# Backup with description
uv run backup.py --game grim_dawn --backup -d "Before boss fight"

# List all backups
uv run backup.py --game grim_dawn --list

# Restore specific backup
uv run backup.py --game grim_dawn --restore 1

# Manage game configurations
uv run backup.py --config

# Cleanup old backups (keep 5 most recent)
uv run backup.py --game grim_dawn --cleanup --keep 5
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--game <id>` | Use specific game from configuration |
| `--save-dir <path>` | Override save directory path |
| `--backup-dir <path>` | Override backup directory path |
| `--max-backups <num>` | Maximum backups to keep |
| `--backup` | Create a backup immediately |
| `-d, --description <text>` | Add description to backup |
| `--restore <num>` | Restore backup by number |
| `--list` | List all available backups |
| `--delete <num>` | Delete specific backup |
| `--cleanup` | Clean up old backups |
| `--keep <num>` | Number of backups to keep during cleanup |
| `--config` | Manage game configurations |

## ⚙️ Configuration

### Game Configuration File

The tool uses `games_config.json` to store game configurations. Here's an example:

```json
{
  "games": {
    "grim_dawn": {
      "name": "Grim Dawn",
      "save_path": "C:\\Users\\username\\OneDrive\\Documents\\My Games\\Grim Dawn\\save",
      "backup_path": "C:\\Util\\save-backups\\backups\\grim_dawn",
      "description": "Action RPG with character builds"
    },
    "skyrim": {
      "name": "The Elder Scrolls V: Skyrim",
      "save_path": "C:\\Users\\username\\Documents\\My Games\\Skyrim\\Saves",
      "backup_path": "C:\\Util\\save-backups\\backups\\skyrim",
      "description": "Open-world RPG adventure"
    }
  },
  "settings": {
    "default_max_backups": 10,
    "auto_expand_paths": true,
    "default_backup_path": "C:\\Util\\save-backups\\backups"
  }
}
```

### Path Expansion

The tool supports automatic path expansion:
- Environment variables: `%USERPROFILE%`, `%DOCUMENTS%`, etc.
- User home directory: `~` expands to user home
- Relative paths from the tool directory

### Adding Games

You can add games through:

1. **Interactive Config Manager**: Run `backup.py --config`
2. **Manual Editing**: Edit `games_config.json` directly (auto-reloads)
3. **Notepad Integration**: Use the built-in Notepad opener with auto-reload

## 🗂️ Backup Structure

Backups are organized with timestamped directories:

```
backups/
├── grim_dawn/
│   ├── backup_20250817_142316/
│   │   ├── .backup_description          # Optional description file
│   │   ├── formulas.gst
│   │   ├── player.gdc
│   │   └── main/
│   │       ├── character1/
│   │       └── character2/
│   ├── backup_20250817_115024/
│   └── backup_20250816_153946/
└── skyrim/
    ├── backup_20250817_100000/
    └── backup_20250816_200000/
```

## 🛡️ Safety Features

- **Pre-restore Backups**: Current state is backed up before restoration
- **Confirmation Prompts**: All destructive operations require confirmation
- **Error Handling**: Robust error handling with informative messages
- **Read-only File Support**: Handles Windows read-only files properly
- **Path Validation**: Checks if directories exist before operations

## 💡 Tips & Best Practices

1. **Regular Backups**: Create backups before major game sessions
2. **Descriptive Names**: Use meaningful descriptions for important saves
3. **Storage Management**: Set appropriate `max_backups` limits
4. **Multiple Games**: Configure all your important games for easy switching
5. **Pre-Boss Backups**: Always backup before challenging encounters
6. **Mod Testing**: Backup before installing new mods
7. **Achievement Runs**: Create milestone backups during achievement runs

## 🔧 File Types

The tool creates several files:

| File | Purpose |
|------|---------|
| `backup.py` | Main Python script |
| `backup.bat` | Windows batch launcher |
| `games_config.json` | User game configurations |
| `games_config.json.default` | Default configuration template |
| `backups/` | Directory containing all backup data |

## 🐛 Troubleshooting

### Common Issues

**Permission Errors**:
- Run as administrator if needed
- Check file/folder permissions
- Close games before backup/restore

**Path Not Found**:
- Verify game installation paths
- Check path expansion in config
- Use absolute paths when in doubt

**Backup Failures**:
- Ensure sufficient disk space
- Close game before backup
- Check antivirus interference

**Config File Issues**:
- Validate JSON syntax
- Check file encoding (UTF-8)
- Restore from `.default` if corrupted

### Debug Information

The tool provides detailed output about:
- Selected game and paths
- Backup sizes and file counts
- Operation progress and timing
- Error details and suggestions

## 🤝 Contributing

Feel free to contribute by:
- Reporting bugs and issues
- Suggesting new features
- Submitting pull requests
- Improving documentation

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed.

## 🙏 Acknowledgments

- Built with Python and the UV package manager
- Designed for Windows gaming environments
- Inspired by the need to protect valuable game save data

---

**Happy Gaming! 🎮** Keep your saves safe and never lose progress again!
