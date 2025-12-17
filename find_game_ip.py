from scapy.all import AsyncSniffer, IP, TCP, UDP
from collections import defaultdict
import time
from datetime import datetime
import os

# =============================
#   CONFIGURAZIONE
# =============================
CAPTURE_DURATION = 30  # Secondi di cattura (puoi modificare)
MIN_PACKETS = 5  # Numero minimo di pacchetti per considerare una connessione

# =============================
#   TRACCIAMENTO CONNESSIONI
# =============================
connections = defaultdict(lambda: {"count": 0, "bytes": 0, "ports": set(), "last_seen": None})

def analyze_packet(packet):
    """Analizza ogni pacchetto e traccia le connessioni"""
    if not packet.haslayer(IP):
        return
    
    ip_layer = packet[IP]
    src_ip = ip_layer.src
    dst_ip = ip_layer.dst
    
    # Ignora traffico locale e broadcast
    if src_ip.startswith("127.") or dst_ip.startswith("127."):
        return
    if src_ip.startswith("169.254.") or dst_ip.startswith("169.254."):
        return
    if dst_ip == "255.255.255.255":
        return
    
    # Determina direzione (OUT = verso server, IN = dal server)
    if src_ip.startswith("192.168.") or src_ip.startswith("10.") or src_ip.startswith("172."):
        # Traffico in uscita (da noi verso server)
        remote_ip = dst_ip
        direction = "OUT"
    else:
        # Traffico in entrata (da server verso noi)
        remote_ip = src_ip
        direction = "IN"
    
    # Estrai porta
    port = None
    if packet.haslayer(TCP):
        port = packet[TCP].dport if direction == "OUT" else packet[TCP].sport
        protocol = "TCP"
    elif packet.haslayer(UDP):
        port = packet[UDP].dport if direction == "OUT" else packet[UDP].sport
        protocol = "UDP"
    else:
        return
    
    # Aggiorna statistiche
    key = remote_ip
    connections[key]["count"] += 1
    connections[key]["bytes"] += len(packet)
    connections[key]["ports"].add(port)
    connections[key]["last_seen"] = datetime.now()
    connections[key]["protocol"] = protocol

def print_results():
    """Stampa i risultati ordinati per numero di pacchetti"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 80)
    print("🔍 ANALISI TRAFFICO DI RETE - Ricerca Server di Gioco")
    print("=" * 80)
    print(f"⏱️  Cattura in corso... (durata: {CAPTURE_DURATION}s)")
    print(f"📊 Connessioni attive monitorate: {len(connections)}\n")
    
    # Ordina per numero di pacchetti (più attivi = più probabili)
    sorted_connections = sorted(
        connections.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )
    
    print(f"{'RANK':<6} {'IP SERVER':<20} {'PORTA(E)':<15} {'PROTO':<8} {'PACCHETTI':<12} {'BYTES':<12}")
    print("-" * 80)
    
    rank = 1
    for ip, stats in sorted_connections:
        if stats["count"] < MIN_PACKETS:
            continue
            
        ports_str = ",".join(str(p) for p in sorted(stats["ports"])[:3])
        if len(stats["ports"]) > 3:
            ports_str += "..."
        
        print(f"{rank:<6} {ip:<20} {ports_str:<15} {stats['protocol']:<8} {stats['count']:<12} {stats['bytes']:<12}")
        rank += 1
        
        if rank > 15:  # Mostra solo i primi 15
            break
    
    print("\n" + "=" * 80)
    print("💡 SUGGERIMENTI:")
    print("   - Le prime righe sono i server più probabili del gioco")
    print("   - Cerca IP con MOLTI pacchetti e porta fissa (es. 443, 80, 8080)")
    print("   - Avvia il gioco ORA per vedere nuove connessioni apparire")
    print("=" * 80)

# =============================
#   MAIN
# =============================
if __name__ == "__main__":
    print("🚀 Avvio monitoraggio traffico di rete...")
    print(f"⏰ Cattura per {CAPTURE_DURATION} secondi")
    print("📱 IMPORTANTE: Avvia il gioco ADESSO per rilevare il server!\n")
    time.sleep(2)
    
    start_time = time.time()
    
    # Cattura pacchetti usando AsyncSniffer (compatibile con Windows senza WinPcap)
    try:
        sniffer = AsyncSniffer(
            prn=analyze_packet,
            store=False,
            filter="tcp or udp"
        )
        
        sniffer.start()
        
        # Aggiorna display ogni secondo
        for i in range(CAPTURE_DURATION):
            time.sleep(1)
            if i % 5 == 0:  # Aggiorna ogni 5 secondi
                print_results()
        
        try:
            sniffer.stop()
        except:
            pass
    except KeyboardInterrupt:
        print("\n\n⚠️  Cattura interrotta dall'utente")
    
    print("\n✅ Cattura completata! Analisi risultati...\n")
    time.sleep(1)
    
    # Stampa risultati finali
    print_results()
    
    # Mostra i top 3 candidati
    sorted_connections = sorted(
        connections.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )
    
    print("\n🎯 TOP 3 CANDIDATI PIÙ PROBABILI:")
    print("-" * 80)
    for i, (ip, stats) in enumerate(sorted_connections[:3], 1):
        if stats["count"] < MIN_PACKETS:
            continue
        most_used_port = max(stats["ports"], key=lambda p: stats["count"]) if stats["ports"] else "N/A"
        print(f"\n{i}. IP: {ip}")
        print(f"   Porta principale: {most_used_port}")
        print(f"   Protocollo: {stats['protocol']}")
        print(f"   Pacchetti: {stats['count']}")
        print(f"   Per usare questo server, aggiorna il file .env con:")
        print(f"   TARGET_IP={ip}")
        print(f"   TARGET_PORT={most_used_port}")
    
    print("\n" + "=" * 80)
    input("\nPremi INVIO per chiudere...")
