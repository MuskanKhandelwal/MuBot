#!/usr/bin/env python3
"""
Project Initialization Script

This script sets up MuBot for first-time use by:
1. Creating the directory structure
2. Generating template memory files (USER.md, MEMORY.md, TOOLS.md)
3. Creating the .env file from .env.example
4. Setting up credentials directories

Run this first before using MuBot:
    python -m scripts.init_project
    
Or if installed:
    mubot-init
"""

import os
import shutil
import sys
from pathlib import Path


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(number: int, text: str):
    """Print a step indicator."""
    print(f"\n[{number}/6] {text}")


def create_directory_structure(base_path: Path) -> bool:
    """Create all necessary directories."""
    dirs = [
        "data/memory",
        "data/vector_store",
        "data/pipelines",
        "credentials",
        "logs",
    ]
    
    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {dir_path}")
    
    return True


def setup_env_file(base_path: Path) -> bool:
    """Create .env file from example if it doesn't exist."""
    env_path = base_path / ".env"
    example_path = base_path / ".env.example"
    
    if env_path.exists():
        print("  ℹ .env already exists, skipping")
        return True
    
    if not example_path.exists():
        print("  ✗ .env.example not found")
        return False
    
    shutil.copy(example_path, env_path)
    print("  ✓ Created .env from template")
    print("  ⚠ IMPORTANT: Edit .env with your API keys and settings")
    
    return True


def initialize_memory_files(base_path: Path) -> bool:
    """Initialize memory system with template files."""
    from mubot.memory.persistence import MemoryInitializer
    
    data_path = base_path / "data"
    initializer = MemoryInitializer(data_path)
    
    if initializer.initialize():
        print("  ✓ Created USER.md")
        print("  ✓ Created MEMORY.md")
        print("  ✓ Created TOOLS.md")
        print("  ✓ Created heartbeat-state.json")
        return True
    else:
        print("  ✗ Failed to initialize memory files")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        import openai
        import chromadb
        import pydantic
        print("  ✓ Core dependencies found")
        return True
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e}")
        print("  Run: pip install -e .")
        return False


def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "=" * 60)
    print("  🎉 Initialization Complete!")
    print("=" * 60)
    print("""
Next Steps:

1. Configure your environment:
   - Edit .env with your API keys
   - Set your Gmail credentials path
   - Configure your sender email

2. Set up Gmail API access:
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Enable Gmail API
   - Create OAuth credentials (Desktop app)
   - Download credentials.json to ./credentials/
   - Rename to gmail_credentials.json

3. Personalize your profile:
   - Edit data/USER.md with your details
   - Update data/MEMORY.md with your job search goals
   - Add your portfolio links to data/TOOLS.md

4. Test the setup:
   python -c "from mubot.agent import JobSearchAgent; import asyncio; \\
             asyncio.run(JobSearchAgent().initialize())"

5. Start using MuBot:
   - Import the agent in your code
   - Draft your first cold email
   - Review and approve before sending

Documentation: See README.md for detailed usage examples.
""")


def main():
    """Main initialization function."""
    print_header("🤖 MuBot - Job Search Cold Emailing Agent")
    print("Setting up your job search assistant...\n")
    
    # Determine base path (project root, not src/mubot)
    # __file__ is in src/mubot/scripts/, so go up 3 levels
    base_path = Path(__file__).parent.parent.parent.parent.resolve()
    print(f"Project directory: {base_path}\n")
    
    # Step 1: Check dependencies
    print_step(1, "Checking dependencies")
    if not check_dependencies():
        print("\n✗ Initialization failed. Please install dependencies first.")
        sys.exit(1)
    
    # Step 2: Create directory structure
    print_step(2, "Creating directory structure")
    create_directory_structure(base_path)
    
    # Step 3: Set up environment file
    print_step(3, "Setting up environment file")
    setup_env_file(base_path)
    
    # Step 4: Initialize memory files
    print_step(4, "Initializing memory system")
    initialize_memory_files(base_path)
    
    # Step 5: Check for credentials directory
    print_step(5, "Setting up credentials directory")
    creds_path = base_path / "credentials"
    creds_path.mkdir(exist_ok=True)
    print(f"  ✓ Created: credentials/")
    print("  ⚠ Place your gmail_credentials.json here")
    
    # Step 6: Create .gitignore
    print_step(6, "Creating .gitignore")
    gitignore_path = base_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Environment variables
.env

# Credentials
credentials/
*.json
!credentials/.gitkeep

# Data files
data/
logs/

# Vector store
*.db
*.sqlite
chroma/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
        gitignore_path.write_text(gitignore_content)
        print("  ✓ Created .gitignore")
    else:
        print("  ℹ .gitignore already exists")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
