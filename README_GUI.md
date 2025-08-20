# Save Game Backup Manager - GUI Version

This is a user-friendly graphical interface for the Save Game Backup Manager, built on top of the existing CLI functionality.

## Features

### 🎮 Game Management
- **Game Selection**: Easy dropdown to select from configured games
- **Game Information Display**: Shows save path, backup path, and description
- **Configuration Management**: Add, edit, and remove game configurations through a visual interface

### 💾 Backup Operations
- **Create Backups**: One-click backup creation with optional descriptions
- **List Backups**: Visual table showing backup date, time, age, size, and descriptions
- **Restore Backups**: Select and restore any backup with confirmation dialog
- **Delete Backups**: Remove unwanted backups with safety confirmation
- **Cleanup Old Backups**: Automatically remove old backups keeping only the most recent ones

### ⚙️ Configuration
- **Visual Game Configuration**: Add/edit games without manually editing JSON files
- **Path Browsing**: Use file dialogs to select save and backup directories
- **Global Settings**: Configure default backup limits and paths
- **Real-time Updates**: Configuration changes are immediately reflected

### 🚀 User Experience
- **Tabbed Interface**: Separate tabs for backup management and configuration
- **Progress Indicators**: Visual feedback during long operations
- **Threading**: Non-blocking operations - GUI remains responsive during backups/restores
- **Error Handling**: Clear error messages and confirmations for all operations
- **Auto-refresh**: Backup list updates automatically every 30 seconds

## Installation

1. Ensure you have Python 3.7+ installed
2. Place `backup_gui.py` in the same directory as `backup.py`
3. The GUI uses the existing `games_config.json` configuration file

## Usage

### Starting the GUI

#### Option 1: Run the batch file
```bash
run_gui.bat
```

#### Option 2: Run directly with Python
```bash
python backup_gui.py
```

### Main Interface

#### Backup Manager Tab
1. **Select Game**: Choose from the dropdown list of configured games
2. **Game Information**: View details about the selected game
3. **Create Backup**: 
   - Enter an optional description
   - Click "💾 Create Backup"
   - Progress bar shows backup progress
4. **Manage Backups**:
   - View all backups in the table
   - Select a backup and use action buttons
   - Restore, delete, or cleanup old backups

#### Game Configuration Tab
1. **View Games**: All configured games shown in a table
2. **Add Game**: Click "➕ Add Game" to open the configuration dialog
3. **Edit Game**: Select a game and click "✏️ Edit Selected"
4. **Remove Game**: Select a game and click "🗑️ Remove Selected"
5. **Global Settings**: Configure default backup limits and paths

### Game Configuration Dialog

When adding or editing a game:

1. **Game ID**: Short identifier (no spaces)
2. **Game Name**: Display name for the game
3. **Save Directory Path**: Where the game stores save files
4. **Backup Directory Path**: Where to store backups (optional)
5. **Description**: Optional description

Use the "Browse" buttons to select directories visually.

## Key Differences from CLI

### Advantages of GUI Version
- **Visual Interface**: No need to remember command-line arguments
- **File Browsing**: Point-and-click directory selection
- **Real-time Feedback**: Progress bars and status updates
- **Error Prevention**: Input validation and confirmation dialogs
- **Bulk Operations**: Easy selection and management of multiple backups
- **Auto-refresh**: Always up-to-date backup listings

### Shared Functionality
- Uses the same `SaveBackupManager` class as CLI
- Reads/writes same `games_config.json` file
- Compatible backup formats
- Same safety features and error handling

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- All dependencies from the original CLI tool

## File Structure

```
save-backups/
├── backup.py              # Original CLI tool
├── backup_gui.py           # GUI application (this file)
├── run_gui.bat            # Windows batch file to launch GUI
├── games_config.json      # Shared configuration file
└── backups/               # Backup storage directory
    └── [game_name]/       # Per-game backup folders
        └── backup_*/      # Individual backup directories
```

## Configuration File

The GUI uses the same `games_config.json` format as the CLI:

```json
{
  "games": {
    "game_id": {
      "name": "Game Name",
      "save_path": "C:\\Path\\To\\Saves",
      "backup_path": "C:\\Path\\To\\Backups",
      "description": "Optional description"
    }
  },
  "settings": {
    "default_max_backups": 10,
    "auto_expand_paths": true,
    "default_backup_path": "./backups"
  }
}
```

## Tips

1. **First Time Setup**: Use the Configuration tab to add your games
2. **Path Variables**: You can use environment variables like `%USERPROFILE%` in paths
3. **Backup Descriptions**: Use meaningful descriptions to remember why you created a backup
4. **Regular Cleanup**: Use the cleanup feature to manage disk space
5. **Safety**: The GUI always asks for confirmation before destructive operations

## Troubleshooting

### GUI Won't Start
- Ensure Python is installed and in PATH
- Check that `backup.py` is in the same directory
- Verify tkinter is available: `python -c "import tkinter"`

### Game Not Listed
- Check the Configuration tab to add games
- Verify paths exist and are accessible
- Check `games_config.json` syntax

### Backup Operations Fail
- Verify save directory exists and is accessible
- Check disk space in backup directory
- Ensure you have write permissions

### Performance Issues
- Large save directories may take time to backup
- Progress bars show operation status
- Operations run in background threads to keep GUI responsive

## Support

For issues or questions:
1. Check the original CLI tool documentation
2. Verify configuration file syntax
3. Test with the CLI version to isolate GUI-specific issues
