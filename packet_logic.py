import json
import sys

class CapturedPacket:
    def __init__(self, timestamp, src, dst, sport, dport, protocol, data):
        self.timestamp = timestamp
        self.src = src
        self.dst = dst
        self.sport = sport
        self.dport = dport
        self.protocol = protocol
        self.data = data

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

class StreamReassembler:
    def __init__(self):
        self.buffer = ""
        self.last_timestamp = ""
        self.json_objects = []

    def add_fragment(self, data_str, timestamp):
        # DEBUG: Stampa cosa sta arrivando (repr mostra caratteri invisibili come \n o \x00)
        print(f"📥 [DEBUG] Fragment ricevuto: {repr(data_str[:50])}... (Len: {len(data_str)})")
        
        if not self.buffer:
            self.last_timestamp = timestamp
        
        self.buffer += data_str
        
        # DEBUG: Stato del buffer attuale
        # print(f"   [DEBUG] Buffer totale attuale: {len(self.buffer)} chars")

        return self.process_buffer()

    def process_buffer(self):
        """
        Tenta di estrarre TUTTI i JSON validi presenti nel buffer usando 
        il conteggio delle parentesi (Brace Counting).
        """
        results = []
        
        while True:
            # 1. Cerchiamo l'inizio di un potenziale JSON
            start_index = self.buffer.find('{')
            
            if start_index == -1:
                # Nessuna graffa aperta.
                # Se il buffer è enorme e senza graffe, puliamo per evitare memory leak
                if len(self.buffer) > 500000:
                    print("⚠️ [DEBUG] Buffer enorme senza JSON, svuoto.")
                    self.buffer = ""
                break # Usciamo dal loop, servono nuovi pacchetti
            
            # 2. Algoritmo Conteggio Parentesi
            brace_count = 0
            end_index = -1
            
            # Scansioniamo dal punto della prima graffa in poi
            for i, char in enumerate(self.buffer[start_index:], start=start_index):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                # Se il conteggio torna a zero, abbiamo trovato la chiusura dell'oggetto
                if brace_count == 0:
                    end_index = i + 1 # +1 per includere la graffa di chiusura
                    break
            
            # 3. Se non abbiamo trovato la fine (end_index è ancora -1), il pacchetto è incompleto
            if end_index == -1:
                print(f"⏳ [DEBUG] JSON incompleto (Graffe aperte: {brace_count}). Attendo next packet.")
                break # Usciamo e aspettiamo altri dati
            
            # 4. Estrazione e Parsing
            candidate_str = self.buffer[start_index:end_index]
            
            try:
                json_obj = json.loads(candidate_str)
                
                print(f"✅ [DEBUG] JSON ESTRATTO CON SUCCESSO! (Len: {len(candidate_str)})")
                
                result_wrapper = {
                    "timestamp": self.last_timestamp,
                    "payload": json_obj
                }
                results.append(result_wrapper)
                
                # 5. Rimuoviamo il JSON estratto dal buffer e continuiamo a ciclare
                # (perché potrebbero esserci altri JSON in coda nello stesso buffer)
                self.buffer = self.buffer[end_index:]
                
                # Resettiamo il timestamp per il prossimo pezzo
                self.last_timestamp = "" 

            except json.JSONDecodeError as e:
                print(f"❌ [DEBUG] Errore parsing su blocco identificato: {e}")
                # Se fallisce il parsing di un blocco che sembrava bilanciato, 
                # probabilmente non era un JSON valido (es. parte di una stringa).
                # Avanziamo di 1 char per riprovare a cercare dalla prossima graffa
                self.buffer = self.buffer[start_index + 1:]
        
        # Se abbiamo trovato qualcosa, ritorniamo l'ultimo o la lista (modifica il main per gestire liste se vuoi)
        # Per compatibilità col tuo main attuale, ritorniamo l'ultimo trovato, 
        # ma l'ideale sarebbe che il main gestisse una lista.
        if results:
            return results[-1] # Ritorna l'ultimo successo per ora
        return None