import json

class CapturedPacket:
    """
    Rappresenta un singolo pacchetto di rete catturato.
    """
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
    """
    Gestisce un buffer per accumulare frammenti TCP e tentare
    di ricostruire un JSON valido da stream frammentati.
    """
    def __init__(self):
        self.buffer = ""
        self.last_timestamp = ""

    def add_fragment(self, data_str, timestamp):
        # Salva il timestamp del primo frammento
        if not self.buffer:
            self.last_timestamp = timestamp
        
        self.buffer += data_str
        return self.try_extract_json()

    def try_extract_json(self):
        # Cerca l'inizio del JSON
        start_index = self.buffer.find('{')
        
        if start_index == -1:
            # Buffer troppo grande senza JSON? Pulizia di sicurezza
            if len(self.buffer) > 1000000: 
                self.buffer = "" 
            return None

        candidate_json = self.buffer[start_index:]

        try:
            # Rimuove caratteri spuri finali tipici di SFS
            clean_candidate = candidate_json.rstrip('%')
            
            # Tenta il parsing
            json_obj = json.loads(clean_candidate)
            
            # Successo!
            result = {
                "timestamp": self.last_timestamp,
                "payload": json_obj
            }
            
            # Reset del buffer
            self.buffer = "" 
            return result

        except json.JSONDecodeError:
            # JSON incompleto, aspetta il prossimo pacchetto
            return None
        except Exception as e:
            print(f"[Reassembler Error] {e}")
            self.buffer = ""
            return None