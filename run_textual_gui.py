#!/usr/bin/env python3
"""
Launcher script for the Textual backup manager GUI
"""

try:
    from backup_gui_textual import main
    main()
except ImportError as e:
    print(f"Error importing Textual GUI: {e}")
    print("Make sure Textual is installed with: uv add textual")
    exit(1)
except Exception as e:
    print(f"Error running Textual GUI: {e}")
    exit(1)
