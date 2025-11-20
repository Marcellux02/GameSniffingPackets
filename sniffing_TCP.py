from scapy.all import AsyncSniffer, Raw
from datetime import datetime
import json
import signal
import sys
import time
import threading
import keyboard
import pyautogui
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# =============================
#   CLASSI & STRUTTURE DATI
# =============================

class CapturedPacket:
    def __init__(self, timestamp, src, dst, sport, dport, protocol, data):
        self.timestamp = timestamp        # string ISO 8601
        self.src = src                    # IP sorgente
        self.dst = dst                    # IP destinazione
        self.sport = sport                # porta sorgente
        self.dport = dport                # porta destinazione
        self.protocol = protocol          # es. TCP/UDP
        self.data = data                  # payload grezzo (stringa)

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "src": self.src,
            "dst": self.dst,
            "sport": self.sport,
            "dport": self.dport,
            "protocol": self.protocol,
            "data": self.data
        }


# Lista globale dei pacchetti catturati
PACKET_STORE = []
INVESTIGATION_PACKETS = []
INVESTIGATION_MODE = False
INVESTIGATION_LOCK = threading.Lock()


# =============================
#   FUNZIONE DI HANDLER
# =============================

def handle_packet(packet):
    timestamp = datetime.now().isoformat()

    # IP layer
    if packet.haslayer("IP"):
        src = packet["IP"].src
        dst = packet["IP"].dst
    else:
        src = None
        dst = None

    # TCP layer
    if packet.haslayer("TCP"):
        sport = packet["TCP"].sport
        dport = packet["TCP"].dport
        protocol = "TCP"

    # UDP layer
    elif packet.haslayer("UDP"):
        sport = packet["UDP"].sport
        dport = packet["UDP"].dport
        protocol = "UDP"

    else:
        sport = None
        dport = None
        protocol = "UNKNOWN"

    # Payload (DATA), può non esserci
    if packet.haslayer(Raw):
        raw_data = packet[Raw].load
        try:
            data_str = raw_data.decode(errors="ignore")
        except:
            data_str = str(raw_data)
    else:
        data_str = ""

    # Filtra pacchetti senza payload
    if len(data_str) == 0:
        return

    # Costruzione della classe
    pkt = CapturedPacket(
        timestamp=timestamp,
        src=src,
        dst=dst,
        sport=sport,
        dport=dport,
        protocol=protocol,
        data=data_str
    )

    PACKET_STORE.append(pkt)

    # Se siamo in modalità investigazione, salva anche lì
    with INVESTIGATION_LOCK:
        if INVESTIGATION_MODE:
            INVESTIGATION_PACKETS.append(pkt)

    # Output live
    print(f"[{timestamp}] {src}:{sport} -> {dst}:{dport} | DATA LEN = {len(data_str)}")
    print(f"DATA (preview): {data_str[:100]}\n")


# =============================
#   SALVATAGGIO JSON
# =============================

def save_to_json(filename="captured_packets.json"):
    total = len(PACKET_STORE)
    print(f"\n📝 Costruzione JSON in corso... ({total} pacchetti)")
    
    packets_data = []
    for i, pkt in enumerate(PACKET_STORE, 1):
        packets_data.append(pkt.to_dict())
        # Barra di progresso ogni 10 pacchetti o all'ultimo
        if i % 10 == 0 or i == total:
            progress = (i / total) * 100
            bar_length = 40
            filled = int(bar_length * i // total)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r[{bar}] {i}/{total} ({progress:.1f}%)", end='', flush=True)
    
    print()  # nuova riga
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(packets_data, f, indent=4)
    
    print(f"💾 Salvati {total} pacchetti in {filename}")


def save_investigation_packets(filename="investigation_packets.json"):
    total = len(INVESTIGATION_PACKETS)
    print(f"\n🔍 Salvataggio pacchetti investigativi... ({total} pacchetti)")
    
    packets_data = []
    for i, pkt in enumerate(INVESTIGATION_PACKETS, 1):
        packets_data.append(pkt.to_dict())
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(packets_data, f, indent=4)
    
    print(f"🔬 Salvati {total} pacchetti investigativi in {filename}")


# =============================
#   INVESTIGAZIONE CON CLICK
# =============================

def investigate_click():
    global INVESTIGATION_MODE, INVESTIGATION_PACKETS
    
    print("\n\n🔬 MODALITÀ INVESTIGAZIONE ATTIVATA!")
    print("⏰ Attesa di 5 secondi prima del click...")
    
    for i in range(5, 0, -1):
        print(f"   {i}...", end='\r', flush=True)
        time.sleep(1)
    
    print("\n🖱️  Esecuzione click del mouse...")
    
    # Resetta i pacchetti investigativi
    with INVESTIGATION_LOCK:
        INVESTIGATION_PACKETS = []
        INVESTIGATION_MODE = True
    
    # Esegue il click
    pyautogui.click()
    
    # Attende mezzo secondo per catturare i pacchetti
    print("📡 Cattura pacchetti in corso (500ms)...")
    time.sleep(0.5)
    
    # Disattiva la modalità investigazione
    with INVESTIGATION_LOCK:
        INVESTIGATION_MODE = False
    
    # Salva i pacchetti catturati
    save_investigation_packets()
    print("✅ Investigazione completata!\n")


# =============================
#   GESTIONE TASTIERA
# =============================

def investigate_click_wrapper():
    global INVESTIGATION_MODE
    
    # Evita trigger multipli se già in corso
    if INVESTIGATION_MODE:
        return

    print("\n⚡ COMBINAZIONE RILEVATA: CTRL+M")
    print("🔬 Investigazione programmata tra 5 secondi...")
    
    # Avvia investigazione in un thread separato
    thread = threading.Thread(target=investigate_click)
    thread.daemon = True
    thread.start()


def start_keyboard_listener():
    # Usa la libreria 'keyboard' per hook globali
    # Suppress=False permette al tasto di essere inviato comunque al sistema
    try:
        keyboard.add_hotkey('ctrl+m', investigate_click_wrapper)
    except ImportError:
        print("Errore: libreria 'keyboard' non trovata. Esegui 'pip install keyboard'")


# =============================
#   LOOP DI SNIFFING
# =============================

if __name__ == "__main__":
    TARGET_IP = os.getenv('TARGET_IP')
    if not TARGET_IP:
        print("Errore: TARGET_IP non trovato nel file .env")
        sys.exit(1)

    print(f"🔍 Avvio sniffing su {TARGET_IP}...")
    print("Premi CTRL+C per interrompere e salvare")
    print("Premi CTRL+M per investigare con click (5s delay + 500ms capture)\n")

    # Avvia il listener della tastiera
    start_keyboard_listener()

    # Crea lo sniffer asincrono
    sniffer = AsyncSniffer(
        filter=f"tcp and ip host {TARGET_IP}",
        prn=handle_packet,
        store=False
    )

    try:
        sniffer.start()
        
        # Loop infinito fino a interruzione
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interruzione rilevata...")
        print("⏳ Arresto dello sniffer...")
        
        sniffer.stop()
        
        save_to_json()
        print("✅ Sniffing interrotto e dati salvati.")
        sys.exit(0)