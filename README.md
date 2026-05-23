# Empire4Kingdoms Protocol Sniffer & Analyzer

A robust set of Python tools designed to intercept, analyze, and decode the network traffic of the mobile application **"Empire: Four Kingdoms"**. It leverages custom TCP stream reassembly to accurately reconstruct fragmented JSON payloads on the fly.

## Project Overview

This toolset acts as a specialized packet sniffer tailored for reverse-engineering game protocols. Since game data (like commander attributes, inventory, and gems) is often transmitted via fragmented JSON structures over raw TCP sockets, standard tools struggle to parse it correctly. This project solves that by capturing the raw TCP traffic using `scapy` and utilizing a custom brace-counting algorithm to reassemble and extract complete, valid JSON objects from the stream.

## Key Features

- **Real-Time Traffic Interception**: Monitors TCP/UDP packets specifically exchanged with the target game server using `scapy`.
- **Intelligent Stream Reassembly**: Transparently handles packet fragmentation across TCP streams via a custom brace-counting algorithm (`StreamReassembler`), outputting perfect JSON objects.
- **Investigation Mode**: Bind a hotkey (`CTRL+M`) to simulate a mouse click and isolate the exact network packets corresponding to a specific UI action in the game.
- **Offline Data Decoding**: Automatically parses the captured JSON dumps to decode complex game structures, such as commanders, bailiffs, and equipment, mapping numerical IDs to human-readable effects.

## Technologies Used

- **Python 3.x**
- **Scapy**: For low-level packet capture and filtering.
- **python-dotenv**: For secure configuration management.
- **keyboard / pyautogui**: For the hotkey-driven investigation mode.

## Architecture & Components

- `main.py`: The CLI orchestrator. It provides a unified interface to run all project modules without calling individual scripts manually.
- `src/`: Contains the core logic scripts:
  - `sniffer_main.py`: Configures the sniffer, handles live packet capture, and pushes data to the reassembler.
  - `packet_logic.py`: Contains the protocol logic and the `StreamReassembler`.
  - `decode_json.py`: An offline analysis script that interprets the reconstructed JSON data.
  - `find_game_ip.py`: A utility to monitor active network connections and automatically identify the target game server IP.
- `effect_map.json`: A configuration mapping file that translates in-game effect IDs into descriptive text (e.g., "Melee Strength").
- `docs/`: Contains additional research and notes regarding mobile app reverse engineering and the game protocol.

## Setup & Installation

### 1. Clone and Prepare
Ensure you have Python 3 installed. Clone the repository and navigate to the root directory.

### 2. Install Dependencies
It is recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory based on `.env.example` (if available) or create one with the following required variables:
```env
TARGET_IP=52.50.192.178
TARGET_PORT=443
```
*(Note: Replace with the actual IP/Port of the game server if it has changed).*

## Usage Guide

The project uses a unified CLI orchestrator (`main.py`) to run all commands. You must execute commands from the project root.

1. **Find Game IP (Optional)**:
   If you don't know the server IP, you can use the built-in network monitor:
   ```bash
   python main.py find-ip
   ```

2. **Start the Sniffer**:
   Run the CLI with administrator/root privileges (required for `scapy` to capture packets):
   ```bash
   python main.py sniff
   ```
3. **Monitor Traffic**: 
   The application will begin capturing and reassembling packets. Data will be saved automatically to the `captured_data/` directory.
4. **Investigation Mode**:
   Press `CTRL+M` to trigger a targeted capture. The script will wait 5 seconds, simulate a click, and isolate the resulting packets.
5. **Stop & Save**:
   Press `CTRL+C` to gracefully terminate the sniffer and flush all buffers to disk.
6. **Analyze the Dump**:
   Run the decoder to process the captured JSON files:
   ```bash
   python main.py decode
   ```
   Parsed data will be exported to the `processed_data/` directory.

## Disclaimer

This project is intended for educational purposes, protocol analysis, and personal research only.
