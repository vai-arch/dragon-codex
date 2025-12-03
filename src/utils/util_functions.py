import subprocess
import sys
from src.utils.logger import get_logger

from pathlib import Path
import shutil

logger = get_logger(__name__)

def copy_files(src_folder, dst_folder, extension=".txt"):
    src = Path(src_folder)
    dst = Path(dst_folder)
    dst.mkdir(parents=True, exist_ok=True)

    for txt_file in src.glob("{extension}"):
        shutil.copy2(txt_file, dst)

def run_command(command, step):
    """Run a command and log results"""
    logger.info("="*70)
    logger.info(f"Running: {command}")
    
    condaFolder = "C:/Users/victor.diaz/AppData/Local/miniconda3/envs/dragon/python.exe "
    
    full_command = condaFolder / command

    try:
        result = subprocess.run(
            str(full_command),
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        logger.info(f"✓ {step} - SUCCESS")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {step} - FAILED")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False