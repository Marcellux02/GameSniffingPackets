import argparse
import subprocess
import sys
import os

def run_script(script_name):
    # Determine the script path inside the src/ directory
    script_path = os.path.join("src", script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Error: Script '{script_path}' not found.")
        sys.exit(1)
        
    try:
        # Run the script using the current Python executable
        subprocess.run([sys.executable, script_path], check=True)
    except KeyboardInterrupt:
        # Silently handle keyboard interrupt to prevent ugly stack traces on CTRL+C
        pass
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: The script {script_name} exited with code {e.returncode}")

def main():
    parser = argparse.ArgumentParser(
        description="Empire4Kingdoms Protocol Sniffer & Analyzer CLI"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands to run",
        required=True
    )

    # Command: sniff
    sniff_parser = subparsers.add_parser(
        "sniff", 
        help="Start the packet sniffer (requires administrator privileges)"
    )

    # Command: decode
    decode_parser = subparsers.add_parser(
        "decode", 
        help="Decode offline JSON data from 'captured_data/reassembled'"
    )

    # Command: find-ip
    find_ip_parser = subparsers.add_parser(
        "find-ip", 
        help="Monitor network to find the game server IP automatically"
    )

    args = parser.parse_args()

    if args.command == "sniff":
        run_script("sniffer_main.py")
    elif args.command == "decode":
        run_script("decode_json.py")
    elif args.command == "find-ip":
        run_script("find_game_ip.py")

if __name__ == "__main__":
    main()
