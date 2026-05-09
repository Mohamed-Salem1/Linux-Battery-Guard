# 🔋 Linux Battery Guard Daemon

A professional-grade, lightweight background utility designed for Linux (specifically optimized for Ubuntu/GNOME) to proactively manage and extend battery health. By monitoring real-time power telemetry, this daemon prevents the two primary causes of lithium-ion degradation: **Overcharging** and **Deep Discharging**.

---

## 🚀 Key Professional Features

* **🔍 Dynamic Hardware Discovery:** Implements automated scanning of the Linux `sysfs` (`/sys/class/power_supply/`) to identify the active battery interface (e.g., `BAT0`, `BAT1`). This ensures cross-device compatibility without manual path configuration.
* **🛡️ Intelligent Threshold Management:** Provides active alerts when reaching the maximum charge ceiling (default: `85%`) and the critical discharge floor (default: `25%`).
* **📝 Enterprise-Grade Logging:** Features a dual-channel logging architecture using Python's `logging` module. It maintains a persistent `.log` file for long-term telemetry while providing standard console output for real-time monitoring.
* **🧱 Defensive & Robust Design:** Engineered with comprehensive error handling to ensure system stability. The daemon gracefully handles hardware disconnects, missing dependencies, or kernel-level telemetry delays.
* **🧠 Anti-Spam State Logic:** Utilizes a state-tracking algorithm to ensure notifications are only triggered once per state change, preventing intrusive user alert fatigue.

---

## 🛠️ Technical Architecture

The daemon operates as a low-overhead background process, polling battery metrics every 5 minutes to ensure zero impact on system resources (CPU/RAM). It leverages `subprocess` to interface with system-level visual and audio notification engines.

### Prerequisites
- **Python 3.10+**
- **libnotify-bin** (System-level desktop alerts)
- **pulseaudio-utils** (High-fidelity audio playback)

---

## 📥 Installation & Deployment

1.  **Clone the project:**
    ```bash
    git clone [https://github.com/Mohamed-Salem1/Battery-Guard.git](https://github.com/Mohamed-Salem1/Battery-Guard.git)
    cd Battery-Guard
    ```

2.  **Grant execution permissions:**
    ```bash
    chmod +x battery_guard.py
    ```

3.  **Deploy as a background process:**
    ```bash
    nohup python3 battery_guard.py > /dev/null 2>&1 &
    ```

---

## ⚙️ Configuration

Thresholds can be easily customized in the `Constants` section of the script:
- `MAX_BATTERY_LEVEL`: Optimal unplug point (Default: 85).
- `MIN_BATTERY_LEVEL`: Optimal plug-in point (Default: 25).
- `CHECK_INTERVAL_SECONDS`: Polling frequency (Default: 300s).

---

## 👨‍💻 Developed By
**Mohamed Salem**
*Cloud & DevOps Engineering Enthusiast*
