"""
Export all codebase files to a single text file for analysis.
Excludes binary files, dependencies, and build artifacts.
"""

import os
from pathlib import Path

# Folders to skip
SKIP_FOLDERS = {
    'node_modules',
    '.git',
    '__pycache__',
    'dist',
    'build',
    '.vscode',
    '.idea',
    'venv',
    '.pytest_cache',
    'coverage',
    '.next',
    'out',
    '.venv',
    'debug',  # Skip all debug folder
}

# File extensions to skip (binary and large files)
SKIP_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd',
    '.so', '.dll', '.dylib',
    '.exe', '.bin',
    '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg', '.webp',
    '.mp4', '.avi', '.mov', '.mp3', '.wav',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx',
    '.lock',  # package-lock.json, yarn.lock
    '.map',   # source maps
    '.woff', '.woff2', '.ttf', '.eot',  # fonts
}

# Specific files to skip
SKIP_FILES = {
    'package-lock.json',
    'yarn.lock',
    'poetry.lock',
    '.DS_Store',
    'Thumbs.db',
    'codebase_export.txt',  # Don't include the export file itself
}

# Max file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def should_skip_path(path: Path, root: Path) -> bool:
    """Check if path should be skipped."""
    # Check if any parent folder is in skip list
    try:
        relative = path.relative_to(root)
        for part in relative.parts:
            if part in SKIP_FOLDERS:
                return True
    except ValueError:
        pass
    
    # Check file extension
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    
    # Check filename
    if path.name in SKIP_FILES:
        return True
    
    # Check file size
    if path.is_file():
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                return True
        except:
            return True
    
    return False


def is_text_file(file_path: Path) -> bool:
    """Check if file is likely a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(512)  # Try reading first 512 bytes
        return True
    except (UnicodeDecodeError, PermissionError):
        return False


def export_codebase(root_folder: str, output_file: str):
    """Export all code files to a single text file."""
    root = Path(root_folder)
    
    if not root.exists():
        print(f"Error: Folder {root_folder} does not exist")
        return
    
    files_processed = 0
    files_skipped = 0
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"# Codebase Export: {root.name}\n")
        out.write(f"# Root: {root.absolute()}\n")
        out.write("=" * 80 + "\n\n")
        
        # Walk through all files
        for file_path in sorted(root.rglob('*')):
            if not file_path.is_file():
                continue
            
            # Skip if needed
            if should_skip_path(file_path, root):
                files_skipped += 1
                continue
            
            # Check if text file
            if not is_text_file(file_path):
                files_skipped += 1
                continue
            
            # Get relative path
            try:
                relative_path = file_path.relative_to(root)
            except ValueError:
                relative_path = file_path
            
            # Write file info
            out.write("\n" + "=" * 80 + "\n")
            out.write(f"FILE: {relative_path}\n")
            out.write(f"PATH: {file_path.absolute()}\n")
            out.write("=" * 80 + "\n\n")
            
            # Write file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    out.write(content)
                    if not content.endswith('\n'):
                        out.write('\n')
                files_processed += 1
                print(f"✓ {relative_path}")
            except Exception as e:
                out.write(f"ERROR: Could not read file - {e}\n")
                print(f"✗ {relative_path} - {e}")
                files_skipped += 1
            
            out.write("\n")
    
    print(f"\n{'='*60}")
    print(f"Export complete!")
    print(f"Files processed: {files_processed}")
    print(f"Files skipped: {files_skipped}")
    print(f"Output file: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    root_folder = r"./"
    output_file = r"codebase_export.txt"
    
    print(f"Exporting codebase from: {root_folder}")
    print(f"Output file: {output_file}")
    print(f"\nProcessing files...\n")
    
    export_codebase(root_folder, output_file)
