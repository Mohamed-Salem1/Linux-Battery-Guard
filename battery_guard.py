"""
Project: Battery Guard (Battery Health Monitor)
Author: Mohamed Salem
Date: May 2026
Description: A robust background daemon for Linux Ubuntu that monitors battery health.
             It alerts the user via critical desktop notifications and audio cues
             when the battery reaches optimal charge limits, helping to prolong
             battery lifespan. Features include dynamic hardware detection,
             state management, and dual-channel logging.
"""

import os
import time
import logging
import subprocess
from typing import Tuple, Optional

# ==========================================
# Global Constants & Configuration
# ==========================================
MAX_BATTERY_LEVEL = 85
MIN_BATTERY_LEVEL = 25
CHECK_INTERVAL_SECONDS = 300  # 300 seconds = 5 minutes
LOG_FILE = "battery_guard.log"
AUDIO_ALERT_FILE = "/usr/share/sounds/freedesktop/stereo/complete.oga"


def setup_logging() -> None:
    """
    Configures a dual-channel logging system.
    Logs are simultaneously written to a local file (for historical tracking)
    and printed to the standard output/console (for real-time debugging).
    """
    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File Handler: Appends logs to the local log file
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    # Console Handler: Outputs logs to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def get_battery_paths() -> Tuple[Optional[str], Optional[str]]:
    """
    Dynamically scans the Linux sysfs (System File System) to locate the active battery.
    This ensures cross-device compatibility (e.g., handling BAT0, BAT1, etc.).

    Returns:
        Tuple containing the path to the capacity file and the status file.
    """
    base_dir = "/sys/class/power_supply/"

    try:
        # Iterate over all directories in the power_supply path
        for item in os.listdir(base_dir):
            if item.startswith("BAT"):
                capacity_path = os.path.join(base_dir, item, "capacity")
                status_path = os.path.join(base_dir, item, "status")

                logging.info(f"Battery interface dynamically detected at: {item}")
                return capacity_path, status_path

        logging.error("Hardware detection failed: No battery directory found.")
        return None, None

    except FileNotFoundError:
        logging.error(f"System path not found: {base_dir}. Is this a standard Linux system?")
        return None, None


def get_battery_info(capacity_path: str, status_path: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Reads the real-time battery capacity percentage and charging state.
    Includes runtime validation to prevent crashes if the battery is suddenly disconnected.
    """
    # Defensive programming: Verify paths still exist before attempting file I/O
    if not os.path.exists(capacity_path):
        logging.warning("Battery path is temporarily inaccessible. Skipping this cycle.")
        return None, None

    try:
        # Read capacity percentage
        with open(capacity_path, "r") as capacity_file:
            capacity = int(capacity_file.read().strip())

        # Read status (Charging / Discharging / Full)
        with open(status_path, "r") as status_file:
            status = status_file.read().strip()

        return capacity, status

    except Exception as e:
        logging.error(f"I/O Error while reading battery metrics: {e}")
        return None, None


def send_notification(title: str, message: str) -> None:
    """
    Dispatches a critical desktop notification and plays a system sound.
    Uses 'check=False' to gracefully handle environments lacking audio/notification tools.
    """
    try:
        # Dispatch visual alert (-u critical prevents auto-dismissal)
        subprocess.run(['notify-send', '-u', 'critical', title, message], check=False)

        # Dispatch audio alert (using the selected 'complete' tone)
        subprocess.run(['paplay', AUDIO_ALERT_FILE], check=False)

    except Exception as e:
        logging.warning(f"Failed to execute external notification commands: {e}")


def monitor_battery() -> None:
    """
    The primary daemon loop. Periodically evaluates battery health metrics against
    defined thresholds and triggers actions accordingly. Manages notification state
    to prevent spamming the user.
    """
    setup_logging()

    logging.info("=" * 60)
    logging.info("Battery Guard Daemon Initialized.")
    logging.info(f"Target Thresholds  -> Max: {MAX_BATTERY_LEVEL}% | Min: {MIN_BATTERY_LEVEL}%")
    logging.info(f"Polling Frequency  -> Every {CHECK_INTERVAL_SECONDS} seconds")
    logging.info("=" * 60)

    # Perform initial hardware discovery
    capacity_path, status_path = get_battery_paths()

    # Graceful exit if hardware is unsupported
    if capacity_path is None or status_path is None:
        print(f"\n[CRITICAL] Initialization failed. Please review '{LOG_FILE}'. Exiting.\n")
        return

    # State variable to remember the last triggered alert
    last_notified_state = None

    # Infinite daemon loop
    while True:
        capacity, status = get_battery_info(capacity_path, status_path)

        if capacity is not None and status is not None:
            logging.info(f"Telemetry -> Battery: {capacity}% | State: {status}")

            # -------------------------------------------------------------
            # Logical Branch 1: Overcharge Protection (High Limit Reached)
            # -------------------------------------------------------------
            if capacity >= MAX_BATTERY_LEVEL and status == "Charging":
                # Only notify if we haven't already sent the 'FULL' alert
                if last_notified_state != "FULL":
                    send_notification(
                        "Battery Guard: High Limit",
                        f"Battery level is {capacity}%. Please unplug the AC adapter."
                    )
                    last_notified_state = "FULL"
                    logging.warning(f"ACTION: Alert Dispatched [Type: HIGH_LIMIT, Level: {capacity}%]")

            # -------------------------------------------------------------
            # Logical Branch 2: Deep Discharge Protection (Low Limit Reached)
            # -------------------------------------------------------------
            elif capacity <= MIN_BATTERY_LEVEL and status == "Discharging":
                # Only notify if we haven't already sent the 'LOW' alert
                if last_notified_state != "LOW":
                    send_notification(
                        "Battery Guard: Low Limit",
                        f"Battery level is {capacity}%. Please plug in the AC adapter."
                    )
                    last_notified_state = "LOW"
                    logging.warning(f"ACTION: Alert Dispatched [Type: LOW_LIMIT, Level: {capacity}%]")

            # -------------------------------------------------------------
            # Logical Branch 3: Safe Zone or Action Taken (State Reset)
            # -------------------------------------------------------------
            else:
                # If battery is within safe margins, or the user has complied
                # (e.g., unplugged the charger), we reset the state to allow future alerts.
                last_notified_state = None

        # Suspend thread execution to conserve CPU cycles and RAM
        time.sleep(CHECK_INTERVAL_SECONDS)


# Standard Python boilerplate to execute the main function
if __name__ == "__main__":
    # Ensure graceful handling if the user manually stops the script (Ctrl+C)
    try:
        monitor_battery()
    except KeyboardInterrupt:
        print("\n[INFO] Battery Guard stopped by user. Goodbye!")
