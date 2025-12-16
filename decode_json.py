import json
import os
import glob
from datetime import datetime

# --- 0. CONFIGURAZIONE UTENTE ---

# True: Salva nel JSON finale "ID: +Valore%" (es: "10003: +80%")
# False: Salva nel JSON finale "Nome: +Valore%" (es: "Forza Mischia: +80%")
EXPORT_RAW_IDS = False

# --- 1. CONFIGURAZIONE GLOBALE ---

EFFECT_MAP = {} # Sarà popolato dal file JSON esterno

SLOT_MAP = {
    1: "Elmo", 2: "Corazza", 3: "Arma", 4: "Artefatto",
    5: "Aspetto", 6: "Eroe", 7: "Gemma"
}

RARITY_MAP_FALLBACK = {
    0: "Comune", 1: "Raro", 2: "Epico", 3: "Leggendario", 4: "Unico", 15: "Aspetto"
}

# --- 2. CARICAMENTO MAPPA ESTERNA ---

def load_effect_map():
    global EFFECT_MAP
    filename = "effect_map.json"
    
    if not os.path.exists(filename):
        print(f"⚠️  ATTENZIONE: File '{filename}' non trovato nella root.")
        print("    Gli effetti verranno visualizzati solo come ID numerici.")
        return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            raw_map = json.load(f)
            # Il JSON ha chiavi stringa ("100"), Python usa int (100). Convertiamo.
            EFFECT_MAP = {int(k): v for k, v in raw_map.items() if k.isdigit()}
        print(f"✅ Mappa effetti caricata: {len(EFFECT_MAP)} definizioni.")
    except Exception as e:
        print(f"❌ Errore caricamento '{filename}': {e}")

# --- 3. FUNZIONI DI ANALISI ---

def get_effect_label(eff_id):
    """Restituisce l'ID o il Nome in base alla configurazione e alla mappa."""
    if EXPORT_RAW_IDS:
        return str(eff_id)
    return EFFECT_MAP.get(eff_id, f"Effetto[{eff_id}]")

def parse_effects(effect_list):
    """Converte la lista effetti grezza."""
    parsed = []
    if not isinstance(effect_list, list): return []
    
    for eff in effect_list:
        if isinstance(eff, list) and len(eff) >= 2:
            eff_id = eff[0]
            val = eff[1]
            
            # Gestione valore potenziato (indice 2 se esiste)
            if len(eff) > 2 and isinstance(eff[2], list) and len(eff[2]) > 0:
                val = eff[2][0]

            label = get_effect_label(eff_id)
            parsed.append(f"{label}: +{val}%")
    return parsed

def analyze_gem(gem_data):
    if not isinstance(gem_data, list) or len(gem_data) < 5: return None
    
    gem_id = gem_data[0]
    gem_effects_raw = []
    # Cerca la lista degli effetti della gemma
    for element in gem_data[1:]:
        if isinstance(element, list) and len(element) > 0 and isinstance(element[0], list):
            gem_effects_raw = element
            break
            
    if not gem_effects_raw and gem_id > 0:
        return {"id": gem_id, "effects": [f"{gem_id}: (Effetti n/d)"]}
    elif not gem_effects_raw:
        return None

    return {
        "id": gem_id,
        "effects": parse_effects(gem_effects_raw)
    }

def analyze_equipment(eq_item):
    if not isinstance(eq_item, list) or len(eq_item) < 6: return None
    
    try:
        item_uid = eq_item[0]
        slot_id = eq_item[1]
        raw_rarity = eq_item[2]
        raw_effects = eq_item[5]
        
        # --- LOGICA RARITÀ ---
        is_relic = False
        has_event_stats = False
        
        if isinstance(raw_effects, list):
            for eff in raw_effects:
                if isinstance(eff, list) and len(eff) > 0:
                    eid = eff[0]
                    if eid >= 10000 or (108 <= eid <= 125): is_relic = True
                    elif 200 <= eid <= 800: has_event_stats = True

        if slot_id == 5: rarity_name = "Aspetto (Unico)"
        elif is_relic: rarity_name = "Reliquia (Azzurro)"
        elif has_event_stats: rarity_name = "Set Unico/Leggendario"
        else: rarity_name = RARITY_MAP_FALLBACK.get(raw_rarity, "Sconosciuto")

        effects_readable = parse_effects(raw_effects)
        
        gem_info = None
        if len(eq_item) > 12:
            gem_info = analyze_gem(eq_item[12])

        return {
            "uid": item_uid,
            "slot_name": SLOT_MAP.get(slot_id, f"Slot {slot_id}"),
            "rarity_name": rarity_name,
            "effects": effects_readable,
            "gem": gem_info
        }
    except Exception:
        return None

# --- 4. ESTRAZIONE DATI ---

def find_data_node(data):
    if isinstance(data, dict):
        if "B" in data or "C" in data: return data
        for key, value in data.items():
            if key in ["items", "payload", "data", "return"]:
                res = find_data_node(value)
                if res: return res
    elif isinstance(data, list):
        for item in data:
            res = find_data_node(item)
            if res: return res
    return None

def extract_list(node, key):
    if not node or key not in node: return []
    val = node[key]
    if isinstance(val, dict) and "items" in val: return val["items"]
    if isinstance(val, list): return val
    return []

def process_game_data(json_input):
    extracted_data = {"commanders": [], "bailiffs": []}
    try:
        data = json.loads(json_input) if isinstance(json_input, str) else json_input
        root = find_data_node(data)
        if not root: return None

        # Comandanti
        cmds = extract_list(root, "C")
        if cmds:
            print(f"\n✅ TROVATI {len(cmds)} COMANDANTI")
            for cmd in cmds:
                if not isinstance(cmd, dict): continue
                c_id = cmd.get('ID')
                c_name = cmd.get('N') or f"Comandante {c_id}"
                
                eq_list = []
                raw_eq = cmd.get("EQ", [])
                if isinstance(raw_eq, dict) and "items" in raw_eq: raw_eq = raw_eq["items"]
                elif isinstance(raw_eq, list): raw_eq = raw_eq
                
                processed_eq = []
                if raw_eq:
                    for item in raw_eq:
                        info = analyze_equipment(item)
                        if info: 
                            processed_eq.append(info)
                            # Stampa preview
                            eff_str = ", ".join(info['effects'][:2])
                            print(f"   🔸 {info['slot_name']} [{info['rarity_name']}] -> {eff_str}...")

                extracted_data["commanders"].append({
                    "id": c_id,
                    "name": c_name,
                    "general_level": cmd.get('L', 0),
                    "has_general": (cmd.get('GID', -1) > -1),
                    "equipment": processed_eq
                })

        # Castellani
        bails = extract_list(root, "B")
        if bails:
            print(f"\n✅ TROVATI {len(bails)} CASTELLANI")
            for bai in bails:
                if not isinstance(bai, dict): continue
                b_id = bai.get('ID')
                
                eq_list = []
                raw_eq = bai.get("EQ", [])
                if isinstance(raw_eq, dict) and "items" in raw_eq: raw_eq = raw_eq["items"]
                elif isinstance(raw_eq, list): raw_eq = raw_eq
                
                processed_eq = []
                if raw_eq:
                    for item in raw_eq:
                        info = analyze_equipment(item)
                        if info: 
                            processed_eq.append(info)
                            # Stampa preview
                            eff_str = ", ".join(info['effects'][:2])
                            print(f"   🔹 {info['slot_name']} [{info['rarity_name']}] -> {eff_str}...")

                extracted_data["bailiffs"].append({
                    "id": b_id,
                    "name": f"Castellano {b_id}",
                    "equipment": processed_eq
                })

        return extracted_data
    except Exception as e:
        print(f"❌ Errore: {e}")
        return None

# --- 5. SALVATAGGIO ---

def save_files(data_list):
    base_dir = "processed_data"
    if not os.path.exists(base_dir): os.makedirs(base_dir)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_str = "ID" if EXPORT_RAW_IDS else "Nomi"
    inv_file = os.path.join(base_dir, f"inventario_{mode_str}_{ts}.json")
    
    try:
        with open(inv_file, "w", encoding="utf-8") as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Inventario ({mode_str}) salvato in: {inv_file}")
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")

def get_latest_file():
    base_dir = "captured_data/reassembled"
    if not os.path.exists(base_dir): return None
    files = glob.glob(os.path.join(base_dir, "*.json"))
    return max(files, key=os.path.getctime) if files else None

if __name__ == "__main__":
    # 1. Carica la mappa effetti dal file JSON esterno
    load_effect_map()

    # 2. Trova e processa il file dati
    latest_file = get_latest_file()
    if latest_file:
        print(f"📂 Analisi file: {latest_file}")
        final_collection = []
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            if isinstance(content, list):
                for msg in content:
                    res = process_game_data(msg.get('payload', msg))
                    if res and (res["commanders"] or res["bailiffs"]):
                        final_collection.append(res)
            else:
                res = process_game_data(content)
                if res: final_collection.append(res)
            
            if final_collection:
                save_files(final_collection)
            else:
                print("⚠️ Nessun dato trovato.")
        except Exception as e:
            print(f"❌ Errore esecuzione: {e}")
    else:
        print("❌ Nessun file dati trovato in 'captured_data/reassembled'.")