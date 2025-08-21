# Textual TUI Version of Save Game Backup Manager

## Overview

This is a terminal-based user interface (TUI) version of the Save Game Backup Manager built with [Textual](https://textual.textualize.io/). 

## Features

### Main Features
- **Game Selection**: Choose from configured games via dropdown
- **Create Backups**: Create timestamped backups with optional descriptions
- **Restore Backups**: Restore save files from any backup
- **Delete Backups**: Remove unwanted backups
- **Cleanup Old Backups**: Automatically remove backups beyond the configured limit
- **Game Configuration**: Add, edit, and remove game configurations
- **Global Settings**: Configure default backup paths and maximum backup counts

### User Interface
- **Tabbed Interface**: Switch between Backup Manager and Configuration tabs
- **Collapsible Sections**: Organized UI with expandable/collapsible sections
- **Data Tables**: Sortable tables for backups and game configurations
- **Modal Dialogs**: Confirmation dialogs and configuration forms
- **Progress Indicators**: Visual feedback during backup operations
- **Keyboard Shortcuts**: Quick access to common functions

## Installation

1. Ensure Textual is installed:
   ```bash
   uv add textual
   ```

2. The Textual GUI is ready to use once textual is installed.

## Usage

### Running the Textual GUI

#### Option 1: Direct Python execution
```bash
python backup_gui_textual.py
```

#### Option 2: Using the launcher script
```bash
python run_textual_gui.py
```

#### Option 3: Using the batch file (Windows)
```cmd
run_textual_gui.bat
```

### Navigation

#### Keyboard Shortcuts
- `q` - Quit application
- `r` - Refresh current view
- `c` - Create backup (when in backup tab)
- `d` - Delete selected backup
- `Tab` - Navigate between UI elements
- `Enter` - Activate buttons or select items
- `Escape` - Close dialogs

#### Mouse Support
- Click buttons to activate them
- Click table rows to select them
- Use scrollbars to navigate large lists

### Main Interface

#### Backup Manager Tab
1. **Game Selection Section**
   - Use the dropdown to select a configured game
   - Game information displays below the selection

2. **Backup Actions Section**
   - Enter an optional description for new backups
   - Click "Create Backup" to create a new backup
   - Click "Refresh" to update the backup list

3. **Available Backups Section**
   - View all available backups in a table
   - Select a backup and use action buttons:
     - "Restore Selected" - Restore the selected backup
     - "Delete Selected" - Delete the selected backup
     - "Cleanup Old Backups" - Remove backups beyond the limit

#### Configuration Tab
1. **Configured Games Section**
   - View all configured games in a table
   - Use action buttons to:
     - "Add Game" - Configure a new game
     - "Edit Selected" - Modify selected game configuration
     - "Remove Selected" - Delete selected game configuration
     - "Refresh" - Update the games list

2. **Global Settings Section**
   - Set default maximum number of backups to keep
   - Set default backup directory path
   - Click "Save Settings" to apply changes

### Adding a New Game

1. Go to the Configuration tab
2. Click "Add Game" button
3. Fill in the dialog form:
   - **Game ID**: Short identifier (no spaces)
   - **Game Name**: Display name for the game
   - **Save Directory Path**: Location of game save files
   - **Backup Directory Path**: Where backups should be stored (optional)
   - **Description**: Optional description of the game
4. Click "OK" to save

### Creating Backups

1. Go to the Backup Manager tab
2. Select a game from the dropdown
3. Optionally enter a description
4. Click "Create Backup"
5. Wait for the progress indicator to complete

### Restoring Backups

1. Select a game from the dropdown
2. Select a backup from the table
3. Click "Restore Selected"
4. Confirm the restoration in the dialog
5. Wait for the process to complete

## Configuration

The Textual GUI uses the same configuration file (`games_config.json`) as the other versions. All settings and game configurations are shared between the tkinter GUI, Textual TUI, and CLI versions.


## Requirements

- Python 3.8+
- Textual library (`uv add textual`)
- Same dependencies as the main backup script

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError: No module named 'textual'`:
```bash
uv add textual
```

### Path Issues
Make sure you're running the script from the correct directory or update the paths in the configuration.

### Permission Errors
Ensure the application has read/write access to:
- Game save directories
- Backup directories
- Configuration file location


