import os
import pickle
import subprocess
import sys
from src.utils.logger import get_logger
import json
from pathlib import Path
import shutil
from typing import List, Dict, Set
from datetime import datetime

from pathlib import Path
import shutil

logger = get_logger(__name__)

def get_object_size_mb(filepath):
    return os.path.getsize(filepath) / (1024 * 1024)

def serialize_object(data, output_file, log: False):

    if (log):
        logger.debug(f"\n💾 Saving object to: {output_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def remove_file(filepath: str):
    """Remove a file safely with proper checks."""
    file_path = Path(filepath)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    if not file_path.is_file():
        print(f"❌ Path exists but is not a file: {file_path}")
        return False

    try:
        file_path.unlink()
        print(f"✅ Removed file: {file_path}")
        return True
    except PermissionError:
        print(f"❌ Permission denied: unable to delete {file_path}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error removing file: {e}")
        return False

def find_files_in_folder(path_folder, extension=".txt", exception=True, recursive=False, ):
    """
    Find files in a folder with a given extension.
    
    Args:
        path_folder (str | Path): Folder to search
        extension (str): Extension filter, e.g. ".txt" or "txt"
        recursive (bool): If True, use rglob() to include subfolders
        
    Returns:
        List[Path]: List of file paths found
    """
    folder = Path(path_folder)

    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder does not exist or is not a directory: {folder}")

    # Normalize extension
    ext = extension.lstrip(".")
    pattern = f"*.{ext}"

    # Choose search strategy
    files = folder.rglob(pattern) if recursive else folder.glob(pattern)

    found_files = list(files)

    if not found_files:
        logger.warning(f"No files found in {folder} with extension: {extension}")
        if exception:
            raise FileNotFoundError(f"No files found in {folder} with extension: {extension}")
    else:
        logger.info(f"Found {len(found_files)} file(s) in {folder} with extension: {extension}")

    return found_files

def copy_files(
    src_folder,
    dst_folder,
    extension=".txt",
    recursive=False,
    overwrite=True,
):
    """
    Copy files from src_folder to dst_folder.
    
    Args:
        src_folder (str | Path): Source folder
        dst_folder (str | Path): Destination folder
        extension (str): Extension filter, e.g. ".txt" or "txt"
        recursive (bool): If True, use rglob() to include subfolders
        overwrite (bool): If False, skip files that already exist
    """

    src = Path(src_folder)
    dst = Path(dst_folder)

    # --- Validate source folder ---
    if not src.exists() or not src.is_dir():
        logger.error(f"Source folder does not exist or is not a directory: {src}")
        return False

    # --- Ensure destination folder exists ---
    dst.mkdir(parents=True, exist_ok=True)

    # Normalize extension
    ext = extension.lstrip(".")
    pattern = f"*.{ext}"

    # Choose search strategy
    files = src.rglob(pattern) if recursive else src.glob(pattern)

    copied_count = 0

    for file_path in files:
        dest_file = dst / file_path.name

        if dest_file.exists() and not overwrite:
            logger.info(f"Skipping existing file: {dest_file}")
            continue

        try:
            shutil.copy2(file_path, dest_file)
            logger.info(f"Copied: {file_path} → {dest_file}")
            copied_count += 1
        except Exception as e:
            logger.error(f"Failed to copy {file_path}: {e}")

    if copied_count == 0:
        logger.warning(f"No files copied from {src} (pattern: {pattern})")
    else:
        logger.info(f"Copied {copied_count} file(s) from {src} → {dst}")

    return True

def load_line_by_line(file):
    """
    Load a file line by line as JSON objects.
    
    Args:
        file (str or Path): Path to the JSONL file. 
    """
    lines = []

    input_file = Path(file)
    
    if not input_file.exists():
        raise FileNotFoundError(f"❌ Error: Text file not found: {file}")
    
    logger.debug(f"📂 Loading file: {file}")
    
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            lines.append(json.loads(line))

    print(f"   Loaded: {len(lines):,} lines")

    return lines
    

def load_text_from_file(file):
    """
    Load text data from a file. Raises FileNotFoundError if the file does not exist.
    
    Args:
        file (str or Path): Path to the text file.  
    """ 
    
    input_file = Path(file)
    
    if not input_file.exists():
        raise FileNotFoundError(f"❌ Error: Text file not found: {file}")
    
    logger.debug(f"📂 Loading file: {file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text_data = f.read()

    logger.info(f"📂 Loaded file: {file}")
    return text_data 
   
def load_json_from_file(file):
    """
    Load JSON data from a file. Raises FileNotFoundError if the file does not exist.
    
    Args:
        file (str or Path): Path to the JSON file.
        
    Returns:
        dict or list: Loaded JSON data.
    """
    input_file = Path(file)
    
    if not input_file.exists():
        raise FileNotFoundError(f"❌ Error: Books file not found: {file}")
    
    logger.debug(f"📂 Loading file: {file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    logger.info(f"📂 Loaded file: {file}")
    return json_data
    
def save_jsonl_to_file(data: List[Dict], output_file, indent: int = None):
    # Save to JSONL
    logger.debug(f"\n💾 Saving {len(data)} chunks to: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for json_element in data:
            f.write(json.dumps(json_element, indent= indent, ensure_ascii=False) + '\n')
    
    logger.info(f"\n💾 Saved {len(data)} json elements to: {output_file}")

def save_json_to_file(data: List[Dict], output_file, indent: int = None):
    # Save to JSON
    logger.debug(f"\n💾 Saving {len(data)} chunks to: {output_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent= indent, ensure_ascii=False)
    
    logger.info(f"\n💾 Saved {len(data)} json elements to: {output_file}")
    
def run_command(command, step):

    start_time = datetime.now()

    logger.info("="*70)
    logger.info(f"Running: {command}")

    python_exe = r"C:/Users/victor.diaz/AppData/Local/miniconda3/envs/dragon/python.exe"

    process = subprocess.Popen(
        [python_exe, "-u", str(command.resolve())],      # -u = unbuffered
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False
    )

    while True:
        chunk = process.stdout.read(1024)  # read 1KB at a time
        if not chunk:
            break
        sys.stdout.write(chunk.decode(errors="replace"))
        sys.stdout.flush()

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    if process.returncode == 0:
        logger.info(f"✓ {step} - SUCCESS in {duration}")
        return True
    else:
        logger.error(f"✗ {step} - FAILED in {duration}", exc_info=True)
        return False