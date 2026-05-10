"""
Project     : Battery Guard (Final Stable Edition)
Author      : Mohamed Salem
Date        : May 2026
Version     : 2.1.0
Description : Advanced Linux background daemon for battery health orchestration.
              Features: Dynamic Polling, Emergency Hibernation, Wear Level Tracking,
              Hot-Reload, and Root-to-User Notification Bridging.
"""

import os
import time
import json
import logging
import logging.handlers
import subprocess
from typing import Tuple, Optional, Dict, Any

# ==========================================
# System Constants & Pathing Strategy
# ==========================================
# These files are managed in the same directory for portable testing
CONFIG_FILE = "config.json"
LOG_FILE = "battery_guard.log"
BASE_SYSFS = "/sys/class/power_supply/"


class BatteryGuard:
    def __init__(self):
        # Configuration and logging initialization
        self.config = self._load_and_validate_config()
        self.setup_logging()

        # State tracking and hardware discovery
        self.last_notified_state = None
        self.capacity_path, self.status_path, self.bat_base = self._discover_hardware()

        # Identity bridge: Used to send alerts from Root to Desktop User
        self.target_user = "mohamed-salem"

    def _load_and_validate_config(self) -> Dict[str, Any]:
        """
        Loads configuration from JSON. Validates threshold logic to ensure
        the daemon doesn't enter an inconsistent state.
        """
        defaults = {
            "MAX_BATTERY_LEVEL": 85,
            "MIN_BATTERY_LEVEL": 25,
            "EMERGENCY_LEVEL": 5,
            "SAFE_POLLING_SECONDS": 300,
            "CRITICAL_POLLING_SECONDS": 60,
            "DYNAMIC_POLLING": True,
            "HIBERNATE_ON_EMERGENCY": False,
            "AUDIO_ALERT_FILE": "/usr/share/sounds/freedesktop/stereo/complete.oga"
        }

        if not os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(defaults, f, indent=4)
                return defaults
            except Exception as e:
                print(f"[ERROR] Failed to write config: {e}")
                return defaults

        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)

            # Defensive logic: Ensure thresholds are sequential
            if not (0 < data.get("EMERGENCY_LEVEL", 5) < data.get("MIN_BATTERY_LEVEL", 25) < data.get(
                    "MAX_BATTERY_LEVEL", 85) <= 100):
                logging.warning("Invalid configuration logic. Reverting to safe defaults.")
                return defaults
            return {**defaults, **data}
        except Exception:
            return defaults

    def setup_logging(self):
        """
        Configures a professional rotating log system to prevent disk exhaustion.
        Files are capped at 1MB with a single backup.
        """
        log_format = "%(asctime)s [%(levelname)s] %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        if logger.hasHandlers():
            logger.handlers.clear()

        # File Handler with Rotation (1MB limit)
        fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=1)
        fh.setFormatter(formatter)

        # Console Handler for real-time monitoring
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    def _discover_hardware(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Probes the sysfs tree to identify the battery hardware interface.
        Supports standard Linux naming conventions (BAT0, BAT1, etc.).
        """
        try:
            for item in os.listdir(BASE_SYSFS):
                if item.startswith("BAT"):
                    path = os.path.join(BASE_SYSFS, item)
                    logging.info(f"Hardware Discovery: Monitoring active interface {item}")
                    return os.path.join(path, "capacity"), os.path.join(path, "status"), path
        except Exception as e:
            logging.error(f"Hardware Discovery: Critical path failure - {e}")
        return None, None, None

    def get_wear_level(self) -> float:
        """
        Determines battery health status by comparing design capacity
        with current full charge capability.
        """
        try:
            current_f = "energy_full" if os.path.exists(os.path.join(self.bat_base, "energy_full")) else "charge_full"
            design_f = "energy_full_design" if os.path.exists(
                os.path.join(self.bat_base, "energy_full_design")) else "charge_full_design"

            with open(os.path.join(self.bat_base, current_f), 'r') as f:
                current = int(f.read().strip())
            with open(os.path.join(self.bat_base, design_f), 'r') as f:
                design = int(f.read().strip())

            return round((current / design) * 100, 2)
        except Exception:
            return 0.0

    def notify(self, title: str, msg: str, urgency: str = "critical"):
        """
        Final Professional Bridge: Executes alerts as the desktop user
        while providing the necessary environment context for GUI/Audio.

        Fix v2.1.1:
        - Added PULSE_SERVER to correctly reach user's PulseAudio socket.
        - Switched from 'sudo -u' to 'su -c' with explicit env vars inline
          to avoid dbus-launch lookup failures inside sudo context.
        """
        try:
            target_user = "mohamed-salem"
            # Standard UID for the first user in Ubuntu is 1000
            user_uid = "1000"

            # Full environment needed for both GUI and Audio from a root process
            env_prefix = (
                f"DISPLAY=:0 "
                f"XDG_RUNTIME_DIR=/run/user/{user_uid} "
                f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user_uid}/bus "
                f"PULSE_SERVER=unix:/run/user/{user_uid}/pulse/native"
            )

            # 1. Dispatch Visual Notification via su -c (avoids dbus-launch lookup)
            notify_cmd = f"{env_prefix} notify-send -u {urgency} '{title}' '{msg}'"
            subprocess.run(
                ['su', '-', target_user, '-c', notify_cmd],
                check=False, capture_output=True
            )

            # 2. Dispatch Audio Alert with PulseAudio socket explicitly set
            audio_cmd = f"{env_prefix} paplay {self.config['AUDIO_ALERT_FILE']}"
            subprocess.run(
                ['su', '-', target_user, '-c', audio_cmd],
                check=False, capture_output=True
            )

        except Exception as e:
            logging.debug(f"UX Bridge: Notification cycle failed - {e}")

    def handle_emergency(self, capacity: int):
        """
        Implements Emergency Protection. Triggers hibernation if battery
        hits the critical floor to prevent hardware damage.
        """
        if capacity <= self.config["EMERGENCY_LEVEL"]:
            logging.critical(f"EMERGENCY: Battery at critical level {capacity}%.")
            if self.config["HIBERNATE_ON_EMERGENCY"]:
                self.notify("EMERGENCY", "System hibernating to protect hardware.")
                time.sleep(5)
                subprocess.run(['systemctl', 'hibernate'], check=False)

    def calculate_polling_interval(self, capacity: int) -> int:
        """
        Dynamic Polling: Optimizes CPU usage by reducing check frequency
        when battery is safe, and increasing it near thresholds.
        """
        if not self.config["DYNAMIC_POLLING"]:
            return self.config["SAFE_POLLING_SECONDS"]

        # High-frequency polling (Critical Zones)
        near_max = abs(capacity - self.config["MAX_BATTERY_LEVEL"]) <= 5
        near_min = abs(capacity - self.config["MIN_BATTERY_LEVEL"]) <= 5

        if near_max or near_min or capacity < self.config["MIN_BATTERY_LEVEL"]:
            return self.config["CRITICAL_POLLING_SECONDS"]

        # Low-frequency polling (Safe Zone)
        return self.config["SAFE_POLLING_SECONDS"]

    def run(self):
        """
        The main daemon lifecycle.
        """
        if not self.capacity_path:
            logging.critical("Daemon Exit: Hardware detection failed.")
            return

        # Startup handshake
        health = self.get_wear_level()
        self.notify("Battery Guard Active",
                    f"Monitoring {health}% Health Battery.\nTarget: {self.config['MIN_BATTERY_LEVEL']}% - {self.config['MAX_BATTERY_LEVEL']}%")

        logging.info(f"Daemon: Initialization successful. Battery Health: {health}%")

        while True:
            try:
                # Support Hot-Reload by reloading config each cycle
                self.config = self._load_and_validate_config()

                with open(self.capacity_path, 'r') as f:
                    cap = int(f.read().strip())
                with open(self.status_path, 'r') as f:
                    stat = f.read().strip()

                logging.info(f"Telemetry: {cap}% | {stat} | Health: {health}%")

                # State Machine Logic
                if cap >= self.config["MAX_BATTERY_LEVEL"] and stat == "Charging":
                    if self.last_notified_state != "FULL":
                        self.notify("Battery Guard: Limit Reached", f"Battery is at {cap}%. Please unplug.")
                        self.last_notified_state = "FULL"

                elif cap <= self.config["MIN_BATTERY_LEVEL"] and stat == "Discharging":
                    if self.last_notified_state != "LOW":
                        self.notify("Battery Guard: Low Battery", f"Battery is at {cap}%. Please charge.")
                        self.last_notified_state = "LOW"
                    self.handle_emergency(cap)

                else:
                    self.last_notified_state = None

                time.sleep(self.calculate_polling_interval(cap))

            except KeyboardInterrupt:
                logging.info("Daemon: User termination received.")
                break
            except Exception as e:
                logging.error(f"Daemon: Operational error - {e}")
                time.sleep(60)


if __name__ == "__main__":
    guard = BatteryGuard()
    guard.run()