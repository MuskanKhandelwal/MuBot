"""
MuBot Unified CLI Package

Provides a single entry point for all MuBot operations:
- Interactive chat mode
- Daemon control
- Campaign management
- Follow-up management
- Status and reporting

This package is designed to be importable without loading
the full MuBot agent dependencies when not needed.
"""

__version__ = "0.1.0"

# Only import main entry points here - defer other imports
# until actually needed to avoid loading heavy dependencies
def main():
    """Main entry point - deferred import to avoid circular dependencies."""
    from mubot.cli.main import main as _main
    return _main()

def cli():
    """CLI alias - deferred import."""
    from mubot.cli.main import cli as _cli
    return _cli()

__all__ = [
    "main",
    "cli",
]
