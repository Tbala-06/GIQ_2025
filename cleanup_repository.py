#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository Cleanup Script
=========================

Safely cleans up redundant files and organizes experimental code.

Usage:
    python cleanup_repository.py --dry-run    # Preview changes
    python cleanup_repository.py --execute    # Actually perform cleanup

Author: GIQ 2025 Team
"""

import os
import shutil
import argparse
from pathlib import Path


class RepositoryCleanup:
    """Clean up repository - delete redundant files, archive experimental code"""

    def __init__(self, repo_root, dry_run=True):
        self.repo_root = Path(repo_root)
        self.dry_run = dry_run
        self.changes = []

    def log_action(self, action, path, reason=""):
        """Log a cleanup action"""
        msg = f"[{action}] {path}"
        if reason:
            msg += f" - {reason}"
        self.changes.append(msg)
        print(msg)

    def delete_file(self, filepath, reason=""):
        """Delete a redundant file"""
        full_path = self.repo_root / filepath

        if not full_path.exists():
            self.log_action("SKIP", filepath, "File does not exist")
            return

        if self.dry_run:
            self.log_action("DRY-RUN DELETE", filepath, reason)
        else:
            full_path.unlink()
            self.log_action("DELETED", filepath, reason)

    def archive_file(self, filepath, archive_dir, reason=""):
        """Move experimental file to archive directory"""
        source = self.repo_root / filepath
        dest_dir = self.repo_root / archive_dir
        dest = dest_dir / source.name

        if not source.exists():
            self.log_action("SKIP", filepath, "File does not exist")
            return

        if self.dry_run:
            self.log_action("DRY-RUN ARCHIVE", f"{filepath} → {archive_dir}", reason)
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            self.log_action("ARCHIVED", f"{filepath} → {dest}", reason)

    def delete_pycache(self):
        """Delete all __pycache__ directories"""
        print("\n" + "="*70)
        print("Cleaning Python cache directories...")
        print("="*70)

        for pycache in self.repo_root.rglob("__pycache__"):
            if self.dry_run:
                self.log_action("DRY-RUN DELETE", pycache, "Python cache")
            else:
                shutil.rmtree(pycache)
                self.log_action("DELETED", pycache, "Python cache")

    def cleanup_redundant_files(self):
        """Delete redundant/duplicate files"""
        print("\n" + "="*70)
        print("Deleting redundant files...")
        print("="*70)

        # Duplicate files
        self.delete_file("bot.log", "Duplicate log file (1.7 MB)")
        self.delete_file("road_painting.db", "Duplicate database")
        self.delete_file("App_codes/bot.log", "Duplicate log file")
        self.delete_file("App_codes/road_painting.db", "Duplicate database")

        # Identical duplicate
        self.delete_file(
            "RPI_codes/cam/testing_backup.py",
            "Identical copy of testing.py (512 lines)"
        )

    def archive_experimental_files(self):
        """Move experimental files to archive folder"""
        print("\n" + "="*70)
        print("Archiving experimental files...")
        print("="*70)

        archive_dir = "RPI_codes/cam/experimental"

        experimental_files = [
            ("RPI_codes/cam/testing_enhanced.py", "Enhanced experimental version"),
            ("RPI_codes/cam/centerline_align.py", "Alternative centerline approach"),
            ("RPI_codes/cam/mask_align.py", "Mask-based alignment approach"),
            ("RPI_codes/cam/debug_centerline.py", "Debug tool version 1"),
            ("RPI_codes/cam/debug_centerline2.py", "Debug tool version 2"),
            ("RPI_codes/cam/CENTERLINE_ALIGNMENT_FIX.md", "Documentation for experimental approach"),
        ]

        for filepath, reason in experimental_files:
            self.archive_file(filepath, archive_dir, reason)

    def create_readme_in_archive(self):
        """Create README in experimental archive"""
        archive_dir = self.repo_root / "RPI_codes/cam/experimental"

        if self.dry_run:
            self.log_action("DRY-RUN CREATE", "experimental/README.md", "Archive documentation")
            return

        archive_dir.mkdir(parents=True, exist_ok=True)

        readme_content = """# Experimental Camera Alignment Approaches

This directory contains experimental and alternative alignment algorithms
that were tested but not used in production.

## Active Production System

The production alignment system is:
- **File**: `../testing.py` (512 lines)
- **Algorithm**: Zone-based yellow pixel detection in orange stencil frame
- **Status**: Active, calibrated, tested

## Experimental Files

### testing_enhanced.py
Enhanced version with additional debugging features. More verbose output
and extra visualization options.

### centerline_align.py
Alternative approach using centerline extraction from road markings.
Calculates angle between stencil center line and marking center line.

### mask_align.py
Mask-based alignment using color overlay analysis.

### debug_centerline.py & debug_centerline2.py
Debug tools for centerline detection algorithm development.

## Why These Are Archived

These experimental approaches were explored during development but
ultimately the simpler zone-based detection in `testing.py` proved
more reliable and easier to calibrate in real-world conditions.

## Usage

These files are preserved for reference and potential future improvements.
To test an experimental approach:

```bash
cd /path/to/RPI_codes/cam/experimental
python testing_enhanced.py  # Or other experimental file
```

**Note**: Experimental files may have different dependencies or
configuration requirements than the production system.

---
**Last Updated**: 2025-11-09
**Archived By**: Repository cleanup script
"""

        readme_path = archive_dir / "README.md"
        readme_path.write_text(readme_content)
        self.log_action("CREATED", readme_path, "Archive documentation")

    def generate_summary(self):
        """Generate cleanup summary"""
        print("\n" + "="*70)
        print("CLEANUP SUMMARY")
        print("="*70)

        print(f"\nTotal actions: {len(self.changes)}")

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No files were actually modified")
            print("   Run with --execute to perform cleanup")
        else:
            print("\n✅ Cleanup completed successfully!")

        print("\n" + "="*70)

    def run(self):
        """Execute full cleanup process"""
        print("="*70)
        print("GIQ 2025 - REPOSITORY CLEANUP")
        print("="*70)

        if self.dry_run:
            print("MODE: DRY RUN (preview only)")
        else:
            print("MODE: EXECUTE (will modify files)")

        print(f"Repository: {self.repo_root}")

        # Execute cleanup steps
        self.delete_pycache()
        self.cleanup_redundant_files()
        self.archive_experimental_files()
        self.create_readme_in_archive()

        # Summary
        self.generate_summary()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Clean up GIQ 2025 repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_repository.py --dry-run     Preview changes
  python cleanup_repository.py --execute     Perform cleanup

The script will:
  1. Delete __pycache__ directories
  2. Delete redundant files (testing_backup.py, duplicate logs/db)
  3. Archive experimental cam/ files to experimental/ folder
  4. Create README.md in experimental archive
"""
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files (default)"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform cleanup (modifies files)"
    )

    args = parser.parse_args()

    # Determine mode
    if args.execute:
        dry_run = False
    else:
        dry_run = True  # Default to dry-run for safety

    # Get repository root (script location)
    repo_root = Path(__file__).parent

    # Run cleanup
    cleanup = RepositoryCleanup(repo_root, dry_run=dry_run)
    cleanup.run()


if __name__ == "__main__":
    main()
