#!/usr/bin/env python3
"""
Demo script showing integration between CLI and GUI versions
of the Save Game Backup Manager
"""

import sys
import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Save Game Backup Manager - Launch CLI or GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py                 # Launch GUI by default
  python launcher.py --gui           # Explicitly launch GUI
  python launcher.py --cli           # Launch CLI
  python launcher.py --cli --game skyrim --backup  # CLI backup command
        """
    )
    
    parser.add_argument("--gui", action="store_true", help="Launch GUI version (default)")
    parser.add_argument("--cli", action="store_true", help="Launch CLI version")
    
    # Parse known args to allow passing through CLI arguments
    args, unknown = parser.parse_known_args()
    
    # Determine which version to launch
    if args.cli:
        # Launch CLI version with any remaining arguments
        print("🎮 Launching Save Game Backup Manager - CLI Version")
        import backup
        
        # Modify sys.argv to pass through remaining arguments
        sys.argv = ["backup.py"] + unknown
        backup.main()
        
    else:
        # Launch GUI version (default)
        print("🎮 Launching Save Game Backup Manager - GUI Version")
        
        # Check if GUI dependencies are available
        try:
            import tkinter as tk
        except ImportError:
            print("❌ Error: tkinter not available. Falling back to CLI version.")
            import backup
            sys.argv = ["backup.py"] + unknown
            backup.main()
            return
        
        # Check if backup_gui.py exists
        gui_path = Path(__file__).parent / "backup_gui.py"
        if not gui_path.exists():
            print("❌ Error: backup_gui.py not found. Falling back to CLI version.")
            import backup
            sys.argv = ["backup.py"] + unknown
            backup.main()
            return
        
        # Launch GUI
        import backup_gui
        backup_gui.main()

if __name__ == "__main__":
    main()
