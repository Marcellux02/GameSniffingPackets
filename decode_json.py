import json
import os
import glob
from datetime import datetime

# --- 1. CONFIGURAZIONE MAPPATURA (Resta uguale) ---
SLOT_MAP = { 1: "Elmo", 2: "Corazza", 3: "Arma", 4: "Artefatto", 5: "Aspetto", 6: "Eroe", 7: "Gemma" }
RARITY_MAP = { 0: "Comune", 1: "Raro", 2: "Epico", 3: "Leggendario", 4: "Unico", 5: "Reliquia", 6: "Eroe Unico", 15: "Aspetto" }

EFFECT_MAP = {
    1: "Difesa Mura", 2: "Difesa Gittata", 3: "Difesa Mischia", 4: "Difesa Porta", 5: "Difesa Fossato",
    10001: "Difesa Mischia", 10002: "Difesa Gittata", 10003: "Forza Mischia", 10004: "Forza Gittata",
    10005: "Mischia (Stranieri)", 10006: "Gittata (Stranieri)",
    10104: "Velocità", 10103: "Rilevamento Tardi", 10113: "Prot. Mura", 10114: "Prot. Porta", 10115: "Prot. Fossato",
    30005: "Gloria", 30004: "Saccheggio"
}

# --- 2. FUNZIONI DI ANALISI ---

def parse_effects(effect_list):
    parsed = []
    if not effect_list: return []
    for eff in effect_list:
        if isinstance(eff, list) and len(eff) >= 2:
            eff_id = eff[0]
            eff_val = eff[1]
            name = EFFECT_MAP.get(eff_id, f"Effetto[{eff_id}]")
            parsed.append(f"{name}: +{eff_val}%")
    return parsed

def analyze_equipment(eq_item):
    if not isinstance(eq_item, list) or len(eq_item) < 6: return None
    try:
        slot = SLOT_MAP.get(eq_item[1], f"Slot {eq_item[1]}")
        rarity = RARITY_MAP.get(eq_item[2], "Sconosciuto")
        effects = parse_effects(eq_item[5]) if isinstance(eq_item[5], list) else []
        return {"slot": slot, "rarity": rarity, "effects": effects}
    except: return None

# --- 3. FUNZIONE DI RICERCA RICORSIVA (IL FIX) ---

def find_data_node(data):
    """
    Cerca ricorsivamente un dizionario che contenga le chiavi 'B' (Castellani)
    e 'C' (Comandanti) dentro liste o dizionari annidati.
    """
    if isinstance(data, dict):
        # Se troviamo un oggetto che ha B o C, abbiamo fatto bingo
        if "B" in data or "C" in data:
            return data
        
        # Altrimenti cerchiamo dentro i valori (es. dentro "payload" o "items")
        for key, value in data.items():
            # Ottimizzazione: cerchiamo solo in chiavi probabili per evitare loop infiniti
            if key in ["items", "payload", "data", "return"]: 
                result = find_data_node(value)
                if result: return result

    elif isinstance(data, list):
        # Se è una lista, controlliamo ogni elemento
        for item in data:
            result = find_data_node(item)
            if result: return result
            
    return None

def extract_items_list(node, key):
    """Estrae la lista di oggetti da una chiave (B o C) gestendo formati diversi."""
    if not node or key not in node:
        return []
    
    target = node[key]
    
    # Caso 1: items[...]: [...] -> Formato Toon convertito (spesso dizionario con chiave 'items')
    if isinstance(target, dict) and "items" in target:
        return target["items"]
    
    # Caso 2: C: [...] -> Lista diretta
    if isinstance(target, list):
        return target
        
    return []

def process_game_data(json_input):
    extracted_data = {"commanders": [], "bailiffs": []}
    try:
        # Gestione input (stringa o oggetto)
        data = json.loads(json_input) if isinstance(json_input, str) else json_input
        
        # 1. TROVA IL NODO GIUSTO
        root_node = find_data_node(data)

        if not root_node:
            return None

        # 2. ESTRAZIONE DATI
        commanders = extract_items_list(root_node, "C")
        bailiffs = extract_items_list(root_node, "B")

        # 3. ANALISI E STAMPA
        if commanders:
            print(f"\n✅ TROVATI {len(commanders)} COMANDANTI:")
            for cmd in commanders:
                if not isinstance(cmd, dict): continue
                
                cmd_obj = {
                    "name": cmd.get('N', 'Senza Nome'),
                    "level": cmd.get('L', '?'),
                    "id": cmd.get('ID'),
                    "equipment": []
                }
                print(f"   👑 {cmd_obj['name']} (Lvl {cmd_obj['level']})")
                
                # Cerca equipaggiamento
                eq_list = []
                if "EQ" in cmd:
                    val = cmd["EQ"]
                    if isinstance(val, dict) and "items" in val: eq_list = val["items"]
                    elif isinstance(val, list): eq_list = val
                
                for item in eq_list:
                    info = analyze_equipment(item)
                    if info:
                        cmd_obj["equipment"].append(info)
                        eff_str = ", ".join(info['effects'][:2]) 
                        print(f"      🔸 {info['slot']} ({info['rarity']}): {eff_str}...")
                
                extracted_data["commanders"].append(cmd_obj)

        if bailiffs:
            print(f"\n✅ TROVATI {len(bailiffs)} CASTELLANI:")
            for bai in bailiffs:
                if not isinstance(bai, dict): continue
                
                bai_obj = {
                    "id": bai.get('ID'),
                    "equipment": []
                }
                print(f"   🏰 Castellano ID: {bai_obj['id']}")
                
                eq_list = []
                if "EQ" in bai:
                    val = bai["EQ"]
                    if isinstance(val, dict) and "items" in val: eq_list = val["items"]
                    elif isinstance(val, list): eq_list = val

                for item in eq_list:
                    info = analyze_equipment(item)
                    if info:
                        bai_obj["equipment"].append(info)
                        eff_str = ", ".join(info['effects'][:2])
                        print(f"      🔹 {info['slot']} ({info['rarity']}): {eff_str}...")
                
                extracted_data["bailiffs"].append(bai_obj)

        if not extracted_data["commanders"] and not extracted_data["bailiffs"]:
            return None
            
        return extracted_data

    except Exception as e:
        print(f"❌ Errore analisi: {e}")
        return None

# --- 4. AVVIO (Logica File) ---

def save_processed_data(data):
    base_dir = "processed_data"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"processed_{timestamp}.json"
    filepath = os.path.join(base_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"\n💾 Dati processati salvati in: {filepath}")

def get_latest_reassembled_file():
    base_dir = "captured_data/reassembled"
    if not os.path.exists(base_dir): return None
    list_of_files = glob.glob(os.path.join(base_dir, "*.json"))
    if not list_of_files: return None
    return max(list_of_files, key=os.path.getctime)

if __name__ == "__main__":
    latest_file = get_latest_reassembled_file()
    
    if latest_file:
        print(f"📂 Analisi del file: {latest_file}")
        all_extracted = []
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                json_content = json.load(f)
                
            if isinstance(json_content, list):
                print(f"ℹ️  Analisi di {len(json_content)} messaggi...")
                for i, msg in enumerate(json_content):
                    data_to_process = msg.get('payload', msg)
                    result = process_game_data(data_to_process)
                    if result:
                        all_extracted.append(result)
            else:
                result = process_game_data(json_content)
                if result:
                    all_extracted.append(result)
            
            if all_extracted:
                save_processed_data(all_extracted)
            else:
                print("\n⚠️ Nessun dato rilevante trovato da salvare.")
                
        except Exception as e:
            print(f"❌ Errore lettura file: {e}")
    else:
        print("❌ Nessun file trovato.")