### 1. Informazioni di Base
*   **Nome del Progetto:** Empire4Kingdoms Protocol Sniffer & Analyzer
*   **Ruolo stimato:** Solo Developer (unico autore: Marcello Mendo)
*   **Periodo/Durata:** 20 Novembre 2025 - 17 Dicembre 2025 (circa 1 mese)
*   **Numero totale di commit:** 8

### 2. Descrizione e Impatto
*   **Sintesi (Elevator Pitch):** Strumenti per intercettare, analizzare e decodificare il traffico di rete dell'applicazione mobile "Empire: Four Kingdoms", con ricostruzione di messaggi JSON frammentati e mappatura degli effetti di gioco.
*   **Funzionalità principali:**
    - Intercettazione traffico TCP/UDP tramite Scapy con configurazione tramite file `.env`
    - Ricostruzione di messaggi JSON frammentati tramite algoritmo di conteggio parentesi (brace counting) in `StreamReassembler`
    - Modalità investigazione mirata (CTRL+M) per isolare eventi specifici
    - Decodifica offline dei dati JSON con mapping ID effetti tramite `effect_map.json`
    - Esportazione strutturata in `captured_data/` (raw, reassembled, investigation) e `processed_data/`

### 3. Stack Tecnologico: Software
*   **Linguaggi:** Python
*   **Framework/Librerie rilevate:** Scapy, python-dotenv, keyboard, pyautogui, mitmproxy, Flask, Requests
*   **Database/Storage:** File system basato su JSON (nessun database rilevato)
*   **Strumenti DevOps/Infrastruttura:** Non rilevato (nessun Dockerfile, GitHub Actions o CI/CD configurato)

### 4. Stack Tecnologico: Hardware & Firmware (Se applicabile)
*   **Microcontrollori/MCU rilevati:** Non rilevato
*   **Protocolli di comunicazione ipotizzati:** TCP, UDP (da codice e documentazione)
*   **Software di progettazione hardware:** Non rilevato

### 5. Sfide Tecniche e Architettura (Tua analisi qualitativa)
*   **Architettura generale:** Struttura modulare con separazione delle responsabilità: `sniffer_main.py` (entry point, cattura pacchetti), `packet_logic.py` (logica core con classi `CapturedPacket` e `StreamReassembler`), `decode_json.py` (analisi offline), `effect_map.json` (mappatura ID effetti). Supporto bidirezionale del traffico con istanze separate di `StreamReassembler` per client e server.
*   **Punto di forza del progetto:** Implementazione robusta di un algoritmo di brace counting per la ricostruzione di messaggi JSON frammentati su stream TCP, gestione dello stato globale con lock per thread safety in modalità investigazione.
