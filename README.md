# Empire4Kingdoms Protocol Sniffer & Analyzer

Questo progetto contiene un set di strumenti per intercettare, analizzare e decodificare il traffico di rete dell'applicazione mobile "Empire: Four Kingdoms".

## Struttura del Progetto

### 1. `sniffer_main.py`
È lo script principale per l'intercettazione del traffico.
- **Funzione**: Utilizza `scapy` per ascoltare i pacchetti TCP/UDP scambiati con il server di gioco.
- **Configurazione**: Legge `TARGET_IP` e `TARGET_PORT` dal file `.env`.
- **Funzionalità**:
    - Cattura i pacchetti grezzi.
    - Ricostruisce i messaggi JSON frammentati (Reassembling) utilizzando la logica definita in `packet_logic.py`.
    - Salva i dati catturati in `captured_data/raw` (pacchetti singoli) e `captured_data/reassembled` (messaggi JSON completi).
    - **Modalità Investigazione**: Premendo `CTRL+M`, simula un click ed esegue una cattura mirata per breve tempo, utile per isolare eventi specifici.

### 2. `packet_logic.py`
Contiene la logica core per la gestione dei pacchetti.
- **`CapturedPacket`**: Classe che definisce la struttura di un singolo pacchetto catturato (timestamp, sorgente, destinazione, dati grezzi).
- **`StreamReassembler`**: Classe fondamentale che gestisce il flusso di dati TCP. Poiché i messaggi JSON possono essere frammentati su più pacchetti TCP o più messaggi possono essere in un singolo pacchetto, questa classe accumula i dati in un buffer e utilizza un algoritmo di conteggio delle parentesi graffe per estrarre oggetti JSON validi e completi.

### 3. `decode_json.py`
Script per l'analisi e la decodifica dei dati JSON catturati (offline).
- **Funzione**: Legge i file JSON esportati e cerca di interpretare le strutture dati del gioco (es. inventario, equipaggiamento, gemme).
- **Mapping**: Utilizza `effect_map.json` per tradurre gli ID numerici degli effetti in nomi leggibili (es. "Forza Mischia").
- **Output**: Genera file JSON processati nella cartella `processed_data`.

### 4. `effect_map.json`
File di mappatura che associa gli ID degli effetti del gioco alle loro descrizioni testuali.

## Come usare

1. **Configurazione**:
   - Assicurati di avere un file `.env` con `TARGET_IP` e `TARGET_PORT` corretti.
   
2. **Sniffing**:
   - Esegui `python sniffer_main.py`.
   - Il programma inizierà a catturare il traffico.
   - Usa `CTRL+M` per la modalità investigazione se necessario.
   - Usa `CTRL+C` per fermare la cattura e salvare i dati.

3. **Analisi**:
   - I dati salvati si trovano in `captured_data/`.
   - Puoi usare `decode_json.py` (o script personalizzati) per analizzare i file JSON ricostruiti.

## Requisiti
Vedi `requirements.txt` per le dipendenze Python necessarie (es. `scapy`, `python-dotenv`, `keyboard`, `pyautogui`).
