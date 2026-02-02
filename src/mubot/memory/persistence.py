"""
Persistence Layer

This module handles the actual reading and writing of data to disk.
It abstracts file operations, providing a clean interface for:
- Markdown files with frontmatter (for human-readable memory)
- JSON files (for structured data)
- Directory management

The persistence layer is designed to be:
- Atomic: Writes are completed before renaming to prevent corruption
- Safe: Creates backups before overwriting
- Versioned: Includes metadata for future migration
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import frontmatter
from pydantic import BaseModel


class FileStore:
    """
    Handles storage and retrieval of Markdown files with YAML frontmatter.
    
    Used for:
    - USER.md
    - MEMORY.md
    - TOOLS.md
    - Daily memory logs (memory/YYYY-MM-DD.md)
    
    The frontmatter contains structured metadata, and the body contains
    human-readable Markdown content.
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize the file store.
        
        Args:
            base_path: Root directory for all file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def read_markdown(self, relative_path: str) -> Optional[tuple[dict, str]]:
        """
        Read a Markdown file with frontmatter.
        
        Args:
            relative_path: Path relative to base_path (e.g., "USER.md")
        
        Returns:
            Tuple of (frontmatter dict, body text) or None if file doesn't exist
        """
        file_path = self.base_path / relative_path
        
        if not file_path.exists():
            return None
        
        try:
            post = frontmatter.load(str(file_path))
            return dict(post.metadata), post.content
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def write_markdown(
        self, 
        relative_path: str, 
        metadata: dict, 
        content: str,
        backup: bool = True
    ) -> bool:
        """
        Write a Markdown file with frontmatter.
        
        Uses atomic write (write to temp, then rename) to prevent corruption.
        
        Args:
            relative_path: Path relative to base_path
            metadata: Dictionary for YAML frontmatter
            content: Markdown body content
            backup: Whether to create a .bak file before overwriting
        
        Returns:
            True if successful, False otherwise
        """
        file_path = self.base_path / relative_path
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists and backup is requested
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup_path)
        
        # Prepare content
        post = frontmatter.Post(content, **metadata)
        
        # Atomic write: write to temp file first
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
            
            # Rename temp file to target (atomic on most systems)
            temp_path.replace(file_path)
            return True
            
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def append_to_markdown(self, relative_path: str, content: str) -> bool:
        """
        Append content to the end of a Markdown file without modifying frontmatter.
        
        Useful for daily logs where we want to add entries incrementally.
        
        Args:
            relative_path: Path relative to base_path
            content: Content to append
        
        Returns:
            True if successful, False otherwise
        """
        result = self.read_markdown(relative_path)
        
        if result is None:
            # File doesn't exist, create new
            metadata = {
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
            return self.write_markdown(relative_path, metadata, content)
        
        metadata, existing_content = result
        new_content = existing_content + "\n\n" + content
        return self.write_markdown(relative_path, metadata, new_content, backup=True)


class JsonStore:
    """
    Handles storage and retrieval of JSON files.
    
    Used for:
    - heartbeat-state.json
    - Pydantic model serialization
    - Structured data that doesn't need human readability
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize the JSON store.
        
        Args:
            base_path: Root directory for JSON files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def read_json(self, relative_path: str) -> Optional[dict]:
        """
        Read a JSON file.
        
        Args:
            relative_path: Path relative to base_path
        
        Returns:
            Parsed JSON dict or None if file doesn't exist
        """
        file_path = self.base_path / relative_path
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def write_json(
        self, 
        relative_path: str, 
        data: dict,
        backup: bool = True,
        indent: int = 2
    ) -> bool:
        """
        Write a JSON file.
        
        Uses atomic write to prevent corruption.
        
        Args:
            relative_path: Path relative to base_path
            data: Dictionary to serialize
            backup: Whether to create a .bak file
            indent: JSON formatting indent level
        
        Returns:
            True if successful, False otherwise
        """
        file_path = self.base_path / relative_path
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup_path)
        
        # Atomic write
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            
            temp_path.replace(file_path)
            return True
            
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def read_pydantic(self, relative_path: str, model_class: type[BaseModel]) -> Optional[BaseModel]:
        """
        Read a JSON file and parse it into a Pydantic model.
        
        Args:
            relative_path: Path relative to base_path
            model_class: Pydantic model class to instantiate
        
        Returns:
            Model instance or None if file doesn't exist or is invalid
        """
        data = self.read_json(relative_path)
        if data is None:
            return None
        
        try:
            return model_class.model_validate(data)
        except Exception as e:
            print(f"Error validating {relative_path} as {model_class.__name__}: {e}")
            return None
    
    def write_pydantic(
        self, 
        relative_path: str, 
        model: BaseModel,
        backup: bool = True
    ) -> bool:
        """
        Write a Pydantic model to a JSON file.
        
        Args:
            relative_path: Path relative to base_path
            model: Pydantic model instance to serialize
            backup: Whether to create a backup
        
        Returns:
            True if successful, False otherwise
        """
        return self.write_json(relative_path, model.model_dump(), backup=backup)


class MemoryInitializer:
    """
    Initializes the memory file structure for new users.
    
    Creates default templates for:
    - USER.md
    - MEMORY.md
    - TOOLS.md
    - Initial directory structure
    """
    
    def __init__(self, base_path: Path):
        self.file_store = FileStore(base_path)
        self.json_store = JsonStore(base_path)
    
    def initialize(self) -> bool:
        """
        Create all default memory files if they don't exist.
        
        Returns:
            True if all files created successfully, False otherwise
        """
        success = True
        
        # Create USER.md template
        if not (self.file_store.base_path / "USER.md").exists():
            success = success and self._create_user_template()
        
        # Create MEMORY.md template
        if not (self.file_store.base_path / "MEMORY.md").exists():
            success = success and self._create_memory_template()
        
        # Create TOOLS.md template
        if not (self.file_store.base_path / "TOOLS.md").exists():
            success = success and self._create_tools_template()
        
        # Create heartbeat-state.json
        if not (self.json_store.base_path / "heartbeat-state.json").exists():
            success = success and self._create_heartbeat_state()
        
        # Create memory directory for daily logs
        (self.file_store.base_path / "memory").mkdir(exist_ok=True)
        
        return success
    
    def _create_user_template(self) -> bool:
        """Create USER.md with template content."""
        metadata = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        content = """# User Profile

## Identity
- **Name**: [Your full name]
- **Email**: [your.email@example.com]
- **Phone**: [optional]
- **Location**: [City, Country]
- **Timezone**: [e.g., America/New_York]

## Professional Background
- **Current Title**: [e.g., Senior Software Engineer]
- **Summary**: [2-3 sentence professional summary]
- **Years of Experience**: [X years]
- **Key Skills**: 
  - [Skill 1]
  - [Skill 2]
  - [Skill 3]

## Links
- **LinkedIn**: [URL]
- **GitHub**: [URL]
- **Portfolio**: [URL]
- **Resume**: [URL or file path]

## Preferences
- **Email Tone**: [formal / friendly / bold]
- **Daily Email Limit**: [default: 20]
- **Preferred Send Times**: [e.g., 9:00 AM, 2:00 PM]

## Job Search Goals
- **Target Roles**: [e.g., Staff Engineer, Engineering Manager]
- **Target Companies**: [dream companies or industries]
- **Target Locations**: [remote, specific cities]
- **Salary Expectations**: [range or "flexible"]

## Email Signature
```
[Your Name]
[Title] | [Company or "Seeking New Opportunities"]
[Phone] | [Email]
[LinkedIn URL]
```
"""
        return self.file_store.write_markdown("USER.md", metadata, content)
    
    def _create_memory_template(self) -> bool:
        """Create MEMORY.md with template content."""
        metadata = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        content = """# Memory: Job Search Context

## Career Goals
<!-- Update as your goals evolve -->
- [ ] Short-term goal (3-6 months)
- [ ] Long-term goal (1-2 years)

## Outreach Rules
<!-- Constraints and guidelines for cold emailing -->
- Maximum [X] emails per day
- Always personalize based on recipient background
- Include unsubscribe option in every email
- Wait at least 5 days before first follow-up
- Stop after 3 follow-ups with no response

## What's Working
<!-- Based on response data, what approaches get replies? -->
- Subject lines that ask questions
- Mentioning specific company achievements
- Keeping emails under 150 words

## What's Not Working
<!-- Patterns to avoid -->
- Generic "I'm interested in your company" openings
- Long paragraphs about career history
- Asking for too much in first email

## Company-Specific Notes
<!-- Learnings about specific companies -->
### [Company Name]
- Best contact: [Name, Title]
- What worked: [specific approach]
- Status: [active / paused / do-not-contact]

## Template Versions
<!-- Iterations of email templates -->
- v1.0: Initial templates
- v1.1: Added shorter subject lines
"""
        return self.file_store.write_markdown("MEMORY.md", metadata, content)
    
    def _create_tools_template(self) -> bool:
        """Create TOOLS.md with template content."""
        metadata = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        content = """# Tools & Resources

## Gmail Labels
<!-- Labels used to organize outreach emails -->
- `outreach/sent` - Initial cold emails sent
- `outreach/replied` - Received responses
- `outreach/no-response` - No reply after follow-ups
- `outreach/rejected` - Explicit rejections
- `outreach/converted` - Led to interviews

## Resume Versions
<!-- Different resumes for different roles -->
- **General**: [path or link]
- **Frontend-focused**: [path or link]
- **Backend-focused**: [path or link]
- **Management**: [path or link]

## Portfolio Links
<!-- Projects to reference in emails -->
- **Project 1**: [name, URL, one-line description]
- **Project 2**: [name, URL, one-line description]

## Email Aliases
<!-- If you use different email addresses -->
- Primary: [email]
- Professional: [email]

## External Tools
<!-- Integration points -->
- Notion database: [link for job pipeline]
- Calendar: [for scheduling interviews]
"""
        return self.file_store.write_markdown("TOOLS.md", metadata, content)
    
    def _create_heartbeat_state(self) -> bool:
        """Create initial heartbeat state file."""
        from mubot.memory.models import HeartbeatState
        
        state = HeartbeatState()
        return self.json_store.write_pydantic("heartbeat-state.json", state)
