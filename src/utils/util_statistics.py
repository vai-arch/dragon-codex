from tabulate import tabulate
from datetime import timedelta

from src.utils.config import Config

def format_metric(key, value):
    """
    Smart formatting based on metric name.
    Extend or override easily.
    """
    if value is None:
        return "—"

    # --- SPECIAL CASE: (value, percentage) ---
    if (
        isinstance(value, (tuple, list))
        and len(value) == 2
        and all(isinstance(v, (int, float)) for v in value)
    ):
        val, pct = value
        return f"{int(val)} ({pct:.1f}%)"
    
    # Convert timedelta automatically
    if isinstance(value, timedelta):
        value = value.total_seconds()

    # --- TIME METRICS ---
    if key.endswith("_time"):
        seconds = float(value)

        # Break apart
        days, seconds = divmod(seconds, 86400)   # 24*60*60
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        seconds_str = f"{seconds:.1f}".rstrip("0").rstrip(".")  # pretty seconds

        parts = []
        if days >= 1:
            parts.append(f"{int(days)}d")
        if hours >= 1 or days > 0:
            parts.append(f"{int(hours)}h")
        if minutes >= 1 or hours > 0 or days > 0:
            parts.append(f"{int(minutes)}m")

        # Always show seconds if everything else is zero
        if seconds > 0 or not parts:
            parts.append(f"{seconds_str}s")

        return " ".join(parts)

    if key.startswith("avg_"):
        return f"{value:.3f}"

    # --- TOKEN METRICS ---
    if key.endswith("_tokens"):
        return f"{int(value)}"

    if key.startswith("max_"):
        return f"{int(value)}"

    # --- AUTO HANDLE NUMBERS ---
    if isinstance(value, float):
        return f"{value:.3f}"

    return str(value)

def tabulate_results(results):

    if isinstance(results, dict):
        results_array = []
        results_array.append(results)
        results = results_array

    # Collect all possible metric keys (columns)
    all_keys = sorted({k for r in results for k in r["metrics"].keys()})

    table = []
    for r in results:
        row = [r["name"]]
        metrics = r["metrics"]

        for key in all_keys:
            value = metrics.get(key)
            row.append(format_metric(key, value))

        table.append(row)

    return all_keys, table

def print_results(results, main_message="RESULTS"):
    """
    Results = list of:
    return {
        "name": "Batch-Procesing-Ollama",
        "metrics":{
            "total_time": duration,
            "avg_time": duration.total_seconds() / BATCH_SIZE,
            "avg_tokens": avg_tokens,
            "max_tokens": -1
        }
    }
    """

    headers, rows = tabulate_results(results)

    print(f"\n=== {main_message} ===\n")
    print(tabulate(rows, headers, tablefmt="grid"))

import logging
from logging.handlers import RotatingFileHandler

def get_stats_logger(logfile="stats.log"):
    logger = logging.getLogger("stats_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # avoid duplicate handlers
        handler = RotatingFileHandler(
            Config().LOG_FOLDER / logfile,
            maxBytes=20_000_000,  # 2 MB per file
            backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def log_results_table(results, log_file="stats",  main_message="RESULTS"):

    logger = get_stats_logger(f"{log_file}.log")

    headers, rows = tabulate_results(results)

    table_str = "\n" + tabulate(rows, headers=headers) + "\n"
    logger.info(table_str)


def log_results(results, log_file="stats",  main_message="RESULTS"):
    
    if isinstance(results, dict):
        results_array = []
        results_array.append(results)
        results = results_array

    logger = get_stats_logger(f"{log_file}.log")

    logger.info(f"=== {main_message} ===")

    for r in results:
        test_name = r.get("name", "unknown_test")
        logger.info(f"[{test_name}]")

        for metric, value in r.get('metrics', {}).items():
            logger.info(f"{metric} : {format_metric(metric, value)}")
        
        logger.info("-" * 40)

from tqdm import tqdm

def progress_bar(iterable, enable=True, **tqdm_kwargs):
    """
    Wrapper around tqdm that can be disabled with a flag.
    
    Args:
        iterable: any iterable
        enable (bool): whether to show the progress bar
        **tqdm_kwargs: forwarded to tqdm() when enabled
    
    Returns:
        iterable or tqdm-wrapped iterable
    """
    if enable:
        return tqdm(iterable, **tqdm_kwargs)
    else:
        # Return a plain iterator (no progress bar)
        return iterable
