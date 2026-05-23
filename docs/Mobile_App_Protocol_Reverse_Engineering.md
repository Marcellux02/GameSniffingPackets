# Technical Retrospective: Traffic Interception and Analysis of Target Game Protocol

## 1. Executive Summary

The objective of this project was to intercept, analyze, and automate the data flow of a specific Android mobile application ("Target Game"). The process evolved from basic HTTP proxying and advanced SSL interception attempts to a final, optimized solution using **passive TCP sniffing**.

It was discovered that the application, despite communicating over port 443, transmits data in **cleartext** (unencrypted), allowing for direct capture and analysis using Python and Scapy without the need for complex Man-in-the-Middle (MITM) attacks or root certificate injection.

## 2. Environment Setup and Infrastructure

### 2.1. Emulator Selection

- **Initial Attempt (BlueStacks 5):**
  - Deployed on Windows filesystem (moved from C: to E: due to storage constraints).
  - **Issue:** While ADB connection was successful, gaining persistent Root access to modify the `/system` partition proved unstable. Config file modifications (`bluestacks.conf`) were automatically reverted by the emulator engine upon restart.
- **Final Solution (LDPlayer 9):**
  - Selected for its native "Enable Root" toggle in settings.
  - **OS Version:** Android 9 (Pie).
  - **Configuration:** Root permission enabled, ADB set to "Open Local Connection".

### 2.2. Network Bridge (ADB)

Traffic redirection was forced via Android Debug Bridge (ADB) since the emulator lacked a native Wi-Fi proxy UI.

- **Command:** `adb shell settings put global http_proxy <HOST_IP>:8080`
- **Reset:** `adb shell settings put global http_proxy :0`

---

## 3. SSL/TLS Interception Strategy

### 3.1. The Trust Issue

Android 7+ (Nougat and later) defaults to trusting only certificates in the System Store (`/system/etc/security/cacerts`), ignoring User Store certificates. The Target Game rejected the connection when the `mitmproxy` CA was installed as a standard user certificate, resulting in SSL Handshake failures.

### 3.2. System Certificate Injection (The "Masking" Technique)

On LDPlayer (Android 9), the system partition uses "System-as-Root" and is mounted as read-only at the kernel level, causing standard `mount -o rw,remount /system` commands to fail.

**Solution:** A volatile overlay using `tmpfs` (temporary file system) was implemented to inject the certificate into the system trust store without permanently modifying the partition image.

**Procedure (executed via Root Shell):**

1.  Create a temporary directory: `/data/local/tmp/certs`
2.  Copy existing system certificates and the user-installed `mitmproxy` certificate into this directory.
3.  Mount a `tmpfs` overlay on top of the system directory:
    `mount -t tmpfs tmpfs /system/etc/security/cacerts`
4.  Populate the overlay with the combined certificates.
5.  Correct SELinux contexts and permissions (`chmod 644`, `chcon`).

_Note: This configuration is volatile and must be re-applied upon every emulator reboot._

---

## 4. Protocol Analysis and Discovery

### 4.1. Traffic Identification

Initial inspection using standard HTTP proxying failed to capture game logic traffic.

- **Tool Used:** PCAPdroid (running locally on the emulator).
- **Discovery:** The Target Game communicates via **Raw TCP** over port **443**.
- **Payload Analysis:** Despite using port 443 (normally implied for HTTPS), the protocol is not standard HTTP/1.1 or HTTP/2. It is a persistent TCP stream exchanging **XML data** wrapped in an SSL layer.

### 4.2. Wireshark Verification & Protocol Discovery

Wireshark and Scapy were used on the host network interface to analyze the traffic.

- **Filter:** `tcp.port == 443 and ip.addr == <GAME_SERVER_IP>`
- **Critical Finding:** Contrary to initial assumptions based on the port number (443), the payload is **NOT encrypted** with SSL/TLS.
- **Result:** The raw TCP stream contains readable XML/JSON data. This revelation shifted the strategy from active interception (MITM) to passive sniffing.

---

## 5. The Pivot: From Reverse Engineering to Lightweight Sniffing

The complex infrastructure described in the previous chapters (Rooted Emulator, Certificate Injection, MITMProxy) served a vital purpose: **Reconnaissance**.

Through that deep analysis, we established three critical facts:

1.  **Target Endpoint:** The game communicates with a specific IP (configured in `.env`) on port `443`.
2.  **Protocol Nature:** Despite using port 443, the traffic is **Raw TCP**, not HTTPS.
3.  **Encryption State:** The payload is **not encrypted**.

**Conclusion:** We can discard the heavy MITM setup. The current solution utilizes simple Python scripts located in this repository to passively sniff and process the traffic based on these findings.

## 6. Current Project Architecture

The solution is now entirely contained within the local Python environment, requiring no special configuration on the emulator or device side.

### 6.1. The Core Sniffer (`sniffer_main.py`)

This is the main entry point. It uses the `scapy` library to listen to the network interface.

- **Configuration:** Loads `TARGET_IP` and `TARGET_PORT` from the `.env` file.
- **Functionality:** Captures packets in real-time without interfering with the connection.

### 6.2. Logic & Reassembly (`packet_logic.py`)

Since TCP streams fragment data, this module handles the reconstruction of messages.

- **StreamReassembler:** Buffers incoming TCP segments and stitches them back together into complete XML/JSON messages.
- **CapturedPacket:** A data structure to normalize packet info for storage.

### 6.3. Investigation Mode

To map specific game actions to network packets, the tool includes an interactive mode.

- **Trigger:** `CTRL+M` (Global Hotkey).
- **Automation:** Uses `pyautogui` to click the screen and `scapy` to capture the immediate network response.

---

## 7. How to Run the Sniffer

1.  **Prerequisites:**

    - Python 3.x installed.
    - Dependencies installed: `pip install -r requirements.txt`
    - `.env` file configured with the target IP/Port.

2.  **Execution:**

    ```bash
    python sniffer_main.py
    ```

3.  **Usage:**
    - **Monitor:** Watch the terminal for real-time packet logs.
    - **Investigate:** Press `CTRL+M` to perform an automated click-and-capture test.
    - **Stop:** Press `CTRL+C` to save all logs to the `captured_data/` folder.
