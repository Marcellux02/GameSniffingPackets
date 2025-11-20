from scapy.all import AsyncSniffer, Raw
from datetime import datetime
import json
import sys
import time
import threading
import keyboard
import pyautogui
import os
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# IMPORTO LE CLASSI DAL PRIMO FILE
from packet_logic import CapturedPacket, StreamReassembler

# =============================
#   CONFIGURAZIONE
# =============================
TARGET_IP = os.getenv("TARGET_IP")
TARGET_PORT = os.getenv("TARGET_PORT")

if not TARGET_IP:
    print("❌ Errore: TARGET_IP non trovato nel file .env")
    sys.exit(1)

OUTPUT_RAW = "captured_packets_raw.json"
OUTPUT_REASSEMBLED = "reassembled_payloads.json"
OUTPUT_INVESTIGATION = "investigation_packets.json"

# =============================
#   STATO GLOBALE
# =============================
PACKET_STORE = []
REASSEMBLED_MESSAGES = []
INVESTIGATION_PACKETS = []

INVESTIGATION_MODE = False
INVESTIGATION_LOCK = threading.Lock()

# Istanza del reassembler (dal file esterno)
reassembler = StreamReassembler()

# =============================
#   LOGICA SNIFFER
# =============================

def handle_packet(packet):
    timestamp = datetime.now().isoformat()

    # Estrazione IP
    if packet.haslayer("IP"):
        src, dst = packet["IP"].src, packet["IP"].dst
    else:
        return

    # Estrazione Porte
    if packet.haslayer("TCP"):
        sport, dport, protocol = packet["TCP"].sport, packet["TCP"].dport, "TCP"
    elif packet.haslayer("UDP"):
        sport, dport, protocol = packet["UDP"].sport, packet["UDP"].dport, "UDP"
    else:
        return

    # Estrazione Dati
    data_str = ""
    if packet.haslayer(Raw):
        try:
            data_str = packet[Raw].load.decode(errors="ignore")
        except:
            data_str = str(packet[Raw].load)

    if not data_str:
        return

    # 1. Creazione oggetto Pacchetto (usando la classe importata)
    pkt = CapturedPacket(timestamp, src, dst, sport, dport, protocol, data_str)
    PACKET_STORE.append(pkt)

    # Gestione Investigazione
    with INVESTIGATION_LOCK:
        if INVESTIGATION_MODE:
            INVESTIGATION_PACKETS.append(pkt)

    # 2. Logica Reassembling (Solo traffico in entrata dal server)
    if src == TARGET_IP:
        json_result = reassembler.add_fragment(data_str, timestamp)
        if json_result:
            size = len(str(json_result['payload']))
            print(f"🧩 [JSON RICOSTRUITO] Dimensione: {size} chars")
            REASSEMBLED_MESSAGES.append(json_result)

# =============================
#   SALVATAGGIO FILE
# =============================

def save_all_data():
    print("\n💾 Salvataggio dati in corso...")
    
    # Salva RAW
    with open(OUTPUT_RAW, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in PACKET_STORE], f, indent=4)
    
    # Salva RICOSTRUITI
    with open(OUTPUT_REASSEMBLED, "w", encoding="utf-8") as f:
        json.dump(REASSEMBLED_MESSAGES, f, indent=4)
        
    print(f"✅ Dati salvati: {len(PACKET_STORE)} raw, {len(REASSEMBLED_MESSAGES)} ricostruiti.")

def save_investigation():
    with open(OUTPUT_INVESTIGATION, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in INVESTIGATION_PACKETS], f, indent=4)
    print(f"🔍 Investigazione salvata in {OUTPUT_INVESTIGATION}")

# =============================
#   INTERAZIONE UTENTE
# =============================

def run_investigation():
    global INVESTIGATION_MODE, INVESTIGATION_PACKETS
    print("\n🔬 INVESTIGAZIONE AVVIATA (Click tra 5s)...")
    time.sleep(5)
    
    print("🖱️  CLICK!")
    pyautogui.click()
    
    with INVESTIGATION_LOCK:
        INVESTIGATION_PACKETS = []
        INVESTIGATION_MODE = True
    
    time.sleep(0.5) # Cattura per 0.5s dopo il click
    
    with INVESTIGATION_LOCK:
        INVESTIGATION_MODE = False
    
    save_investigation()
    print("✅ Investigazione conclusa.\n")

def trigger_investigation():
    if not INVESTIGATION_MODE:
        threading.Thread(target=run_investigation, daemon=True).start()

# =============================
#   MAIN
# =============================

if __name__ == "__main__":
    print(f"🚀 Sniffer attivo su {TARGET_IP}")
    
    # Costruzione filtro
    sniff_filter = f"tcp and host {TARGET_IP}"
    if TARGET_PORT:
        sniff_filter += f" and port {TARGET_PORT}"
        print(f"🎯 Filtro porta attivo: {TARGET_PORT}")

    print("CMD: [CTRL+C] Stop & Save | [CTRL+M] Click & Investigate")

    try:
        keyboard.add_hotkey('ctrl+m', trigger_investigation)
    except ImportError:
        print("⚠️ Libreria 'keyboard' non trovata (pip install keyboard)")

    sniffer = AsyncSniffer(
        filter=sniff_filter,
        prn=handle_packet,
        store=False
    )

    try:
        sniffer.start()
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Arresto richiesto...")
        sniffer.stop()
        save_all_data()
        sys.exit(0)