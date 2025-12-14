import logging
from datetime import timedelta
from logging.handlers import RotatingFileHandler

from tabulate import tabulate
from tqdm import tqdm

from src.utils.config import get_config

config = get_config()


def format_metric(key, value):
    """
    Smart formatting based on metric name.
    Extend or override easily.
    """
    if value is None:
        return "—"

    # --- SPECIAL CASE: (value, percentage) ---
    if isinstance(value, (tuple, list)) and len(value) == 2 and all(isinstance(v, (int, float)) for v in value):
        val, pct = value
        return f"{int(val)} ({pct:.1f}%)"

    # Convert timedelta automatically
    if isinstance(value, timedelta):
        value = value.total_seconds()

    # --- TIME METRICS ---
    if key.endswith("_time"):
        seconds = float(value)

        # Break apart
        days, seconds = divmod(seconds, 86400)  # 24*60*60
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


def tabulate_2_levels(results):
    """
    Tabulate a list of books, each with a 'name' and 'metrics' per chapter.

    books_results: list of dicts
        Each dict represents a book:
        {
            "book_name": "Book Title",
            "chapters": [
                {
                    "name": "chapter 1",
                    "metrics": {...}
                },
                ...
            ]
        }
    """
    for book in results:
        book_name = book.get("level_1", "")
        chapters = book.get("level_2", [])

        print(f"\n=== {book_name} ===\n")

        if not chapters:
            print("No chapters found.")
            continue

        # Use your existing tabulate_results logic
        headers, table = tabulate_results(chapters)
        print(tabulate(table, headers=headers, tablefmt="grid"))


def tabulate_results(results):
    if isinstance(results, dict):
        results_array = []
        results_array.append(results)
        results = results_array

    # Collect all possible metric keys (columns)
    all_keys = list(results[0]["metrics"].keys())

    table = []
    for r in results:
        row = [r["name"]]
        metrics = r["metrics"]

        for key in all_keys:
            value = metrics.get(key)
            row.append(format_metric(key, value))

        table.append(row)

    return all_keys, table


def print_processed_time(total_time):
    formatted_time = format_metric("total_time", total_time)
    print(f"Total Duration: {formatted_time}")


# def print_results_table(results, main_message=""):
#     """
#     Print a table of results. Automatically detects:
#     - Single-level: list of chapters with 'name' and 'metrics'
#     - Multi-level: list of books, each containing 'book_name' and chapters

#     Args:
#         results: list or dict
#         main_message: optional title to print above the table
#     """
#     # Determine if it's multi-level (books)
#     if isinstance(results, list) and results and "level_1" in results[0]:
#         # Multi-level: iterate over books
#         for book in results:
#             level_1 = book.get("level_1", "")
#             level_2 = book.get("level_2", [])

#             if main_message:
#                 print(f"\n=== {main_message} - {level_1} ===\n")
#             else:
#                 print(f"\n=== {level_1} ===\n")

#             if not level_2:
#                 print("No chapters found.")
#                 continue

#             headers, rows = tabulate_results(level_2)
#             print(tabulate(rows, headers, tablefmt="grid"))
#     else:
#         # Single-level
#         headers, rows = tabulate_results(results)
#         if main_message:
#             print(f"\n=== {main_message} ===\n")
#         print(tabulate(rows, headers, tablefmt="grid"))


def print_results_table(results, main_message=""):
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

    if main_message != "":
        print(f"\n=== {main_message} ===\n")
    print(tabulate(rows, headers, tablefmt="grid"))


# def print_results(results, main_message=""):
#     """
#     Print results line by line.

#     Args:
#         results: list of dicts in the format:
#             {
#                 "name": "Batch-Processing-Ollama",
#                 "metrics": {
#                     "total_time": duration,
#                     "avg_time": duration.total_seconds() / BATCH_SIZE,
#                     "avg_tokens": avg_tokens,
#                     "max_tokens": -1
#                 }
#             }
#         main_message: optional header message
#     """
#     if isinstance(results, dict):
#         results_array = []
#         results_array.append(results)
#         results = results_array

#     if main_message:
#         print(f"\n=== {main_message} ===\n")

#     for r in results:
#         name = r.get("name", "Unknown")
#         print(f"[{name}]")
#         metrics = r.get("metrics", {})
#         for key, value in metrics.items():
#             print(f"  {key}: {value}")
#         print("-" * 40)


def reset_log(log_file):
    """
    Removes the current log file and resets the logger so a fresh
    file is created the next time get_stats_logger() is called.
    """
    log_path = config.LOG_STATISTICS_FOLDER / f"{log_file}.log"

    # Remove the file if it exists
    if log_path.exists():
        log_path.unlink()

    # Reset the logger's handlers so Python does not keep old file handles open
    logger = logging.getLogger("stats_logger")
    logger.handlers.clear()


def get_stats_logger(logfile="stats.log"):
    logger = logging.getLogger("stats_logger")
    logger.setLevel(logging.INFO)

    if not logger.handlers:  # avoid duplicate handlers
        handler = RotatingFileHandler(
            config.LOG_STATISTICS_FOLDER / logfile,
            maxBytes=20_000_000,  # 2 MB per file
            backupCount=5,
        )
        formatter = logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_results_table(results, log_file="stats", main_message="RESULTS"):
    logger = get_stats_logger(f"{log_file}.log")

    headers, rows = tabulate_results(results)

    table_str = "\n" + tabulate(rows, headers=headers) + "\n"
    logger.info(table_str)


def log_results(results, log_file="stats", main_message="RESULTS"):
    if isinstance(results, dict):
        results_array = []
        results_array.append(results)
        results = results_array

    logger = get_stats_logger(f"{log_file}.log")

    logger.info(f"=== {main_message} ===")

    for r in results:
        test_name = r.get("name", "unknown_test")
        logger.info(f"[{test_name}]")

        for metric, value in r.get("metrics", {}).items():
            logger.info(f"{metric} : {format_metric(metric, value)}")

        logger.info("-" * 40)


def log_processed_time(log_file, total_time):
    formatted_time = format_metric("total_time", total_time)
    logger = get_stats_logger(f"{log_file}.log")
    logger.info(f"Total Duration: {formatted_time}")


def total_statistics_logging(statistics, total_time, title, log_name):
    print_results_table(statistics, title.upper())
    print_processed_time(total_time)

    reset_log(log_name)

    log_results(statistics, log_name, title.upper())
    log_results_table(statistics, log_name, title.upper())
    log_processed_time(log_name, total_time)


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
