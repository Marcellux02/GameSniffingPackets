import json
import os
import glob
from datetime import datetime

# --- 1. CONFIGURAZIONE MAPPATURA ---

SLOT_MAP = {
    1: "Elmo",
    2: "Corazza",
    3: "Arma",
    4: "Artefatto",
    5: "Aspetto", # Rarità solitamente 4 (Unico) o 15
    6: "Eroe",
    7: "Gemma"
}

RARITY_MAP = {
    0: "Comune (Grigio)",
    1: "Raro (Verde)",
    2: "Epico (Viola)",
    3: "Leggendario (Arancione)",
    4: "Unico (Rosso)",     # Include anche gli Aspetti
    5: "Reliquia (Azzurro)",
    6: "Eroe Unico",
    15: "Speciale/Aspetto"
}

# Dizionario esteso per rendere l'output più user friendly
EFFECT_MAP = {
    # Statistiche Base
    1: "Difesa Mura",
    2: "Difesa Gittata",
    3: "Difesa Mischia",
    4: "Difesa Porta",
    5: "Difesa Fossato",
    # Statistiche Avanzate / Eroe
    10001: "Difesa Mischia",
    10002: "Difesa Gittata",
    10003: "Forza Mischia",
    10004: "Forza Gittata",
    10005: "Mischia (vs Stranieri)",
    10006: "Gittata (vs Stranieri)",
    10007: "Mischia (vs Corvi)",
    10008: "Gittata (vs Corvi)",
    10101: "Gloria guadagnata",
    10102: "Risorse saccheggiate",
    10103: "Rilevamento esercito tardivo",
    10104: "Velocità di movimento",
    10113: "Protezione Mura",
    10114: "Protezione Porta",
    10115: "Protezione Fossato",
    10116: "Mura (vs Stranieri)",
    10117: "Porta (vs Stranieri)",
    10118: "Fossato (vs Stranieri)",
    10501: "Limite Unità Fianchi",
    10502: "Limite Unità Fronte",
    10506: "Forza nel Cortile",
    # Gemme o Effetti Eroe (Range 800+)
    801: "Forza Cortile (Gemma/Eroe)",
    802: "Forza Mischia (Gemma/Eroe)",
    806: "Forza Gittata (Gemma/Eroe)",
    809: "Mura (Gemma/Eroe)",
    810: "Porta (Gemma/Eroe)",
    # Economia
    30005: "Bonus Gloria",
    30004: "Capacità Saccheggio"
}

# --- 2. FUNZIONI DI ANALISI ---

def parse_effects(effect_list):
    """
    Converte la lista effetti.
    Formato tipico input: [[ID, ValBase, [ValTotale]], [ID, ValBase]]
    """
    parsed = []
    if not effect_list:
        return []
    
    for eff in effect_list:
        if isinstance(eff, list) and len(eff) >= 2:
            eff_id = eff[0]
            base_val = eff[1]
            
            # Controllo se c'è un valore totale potenziato (indice 2, lista annidata)
            total_val = base_val
            is_boosted = False
            
            if len(eff) > 2 and isinstance(eff[2], list) and len(eff[2]) > 0:
                total_val = eff[2][0]
                is_boosted = True

            name = EFFECT_MAP.get(eff_id, f"Effetto[{eff_id}]")
            
            # Formattazione stringa valore
            val_str = f"+{total_val}%"
            if is_boosted and total_val != base_val:
                val_str += f" (Base {base_val}%)"
                
            parsed.append(f"{name}: {val_str}")
            
    return parsed

def analyze_equipment(eq_item):
    """
    Analizza un singolo pezzo di equipaggiamento.
    Struttura attesa: [UID, Slot, Rarità, Livello, ?, [Lista Effetti], ...]
    """
    if not isinstance(eq_item, list) or len(eq_item) < 6:
        return None
    
    try:
        slot_id = eq_item[1]
        rarity_id = eq_item[2]
        
        slot_name = SLOT_MAP.get(slot_id, f"Slot {slot_id}")
        rarity_name = RARITY_MAP.get(rarity_id, "Sconosciuto")
        
        # Gli effetti sono solitamente all'indice 5
        raw_effects = eq_item[5]
        effects_readable = parse_effects(raw_effects) if isinstance(raw_effects, list) else []
        
        # Controllo rapido se ha una gemma (spesso indice 7 o annidata)
        has_gem = False
        if len(eq_item) > 7 and isinstance(eq_item[7], list) and len(eq_item[7]) > 0:
            has_gem = True
        
        # Se è un pezzo Reliquia (Rarità 5) o Eroe (Slot 6), lo segniamo
        is_relic = (rarity_id == 5)
        
        return {
            "slot_id": slot_id,
            "slot_name": slot_name,
            "rarity_id": rarity_id,
            "rarity_name": rarity_name,
            "is_relic": is_relic,
            "has_gem": has_gem,
            "effects": effects_readable
        }
    except Exception:
        return None

# --- 3. RICERCA E ESTRAZIONE ---

def find_data_node(data):
    """Cerca ricorsivamente il nodo contenente 'B' e 'C'."""
    if isinstance(data, dict):
        if "B" in data and "C" in data:
            return data
        for key, value in data.items():
            if key in ["items", "payload", "data", "return"]:
                res = find_data_node(value)
                if res: return res
    elif isinstance(data, list):
        for item in data:
            res = find_data_node(item)
            if res: return res
    return None

def extract_items_list(node, key):
    """Estrae la lista in modo sicuro (gestendo dict con chiave 'items' o liste dirette)."""
    if not node or key not in node:
        return []
    val = node[key]
    if isinstance(val, dict) and "items" in val:
        return val["items"]
    elif isinstance(val, list):
        return val
    return []

def process_game_data(json_input):
    extracted_data = {"commanders": [], "bailiffs": []}
    
    try:
        data = json.loads(json_input) if isinstance(json_input, str) else json_input
        root_node = find_data_node(data)
        
        if not root_node:
            return None

        commanders = extract_items_list(root_node, "C")
        bailiffs = extract_items_list(root_node, "B")

        # --- ELABORAZIONE COMANDANTI ---
        if commanders:
            print(f"\n✅ TROVATI {len(commanders)} COMANDANTI:")
            for cmd in commanders:
                if not isinstance(cmd, dict): continue
                
                # Logica Nome: Se 'N' è vuoto, usa l'ID
                c_name = cmd.get('N', '')
                c_id = cmd.get('ID')
                if not c_name:
                    c_name = f"Comandante {c_id}"
                
                # Livello Generale
                gen_level = cmd.get('L', 0)
                
                # Generale Associato (GID)
                gid = cmd.get('GID', -1)
                has_general = "Sì" if gid > -1 else "No"
                
                print(f"   👑 {c_name} [ID: {c_id}]")
                print(f"      Generale Livello: {gen_level} | Generale Associato: {has_general} (GID: {gid})")
                
                # Equipaggiamento
                eq_raw = cmd.get("EQ", [])
                # Normalizzazione EQ (potrebbe essere dict o list)
                if isinstance(eq_raw, dict) and "items" in eq_raw: eq_raw = eq_raw["items"]
                
                cmd_obj = {
                    "name": c_name,
                    "id": c_id,
                    "general_level": gen_level,
                    "has_general": (gid > -1),
                    "equipment": []
                }

                if not eq_raw:
                    print("      ⚠️ Nessun equipaggiamento")
                else:
                    for item in eq_raw:
                        info = analyze_equipment(item)
                        if info:
                            cmd_obj["equipment"].append(info)
                            # Stampa user friendly
                            eff_str = " | ".join(info['effects'][:2]) # Solo i primi 2 effetti per non intasare
                            if len(info['effects']) > 2: eff_str += "..."
                            
                            gem_icon = "💎" if info['has_gem'] else ""
                            print(f"      🔸 {info['slot_name']:<10} ({info['rarity_name']}) {gem_icon} -> {eff_str}")
                
                extracted_data["commanders"].append(cmd_obj)

        # --- ELABORAZIONE CASTELLANI ---
        if bailiffs:
            print(f"\n✅ TROVATI {len(bailiffs)} CASTELLANI:")
            for bai in bailiffs:
                if not isinstance(bai, dict): continue
                
                b_id = bai.get('ID')
                b_name = f"Castellano {b_id}" # I castellani raramente hanno nomi
                
                print(f"   🏰 {b_name} [ID: {b_id}]")
                
                eq_raw = bai.get("EQ", [])
                if isinstance(eq_raw, dict) and "items" in eq_raw: eq_raw = eq_raw["items"]

                bai_obj = {"name": b_name, "id": b_id, "equipment": []}

                if not eq_raw:
                    print("      ⚠️ Nessun equipaggiamento")
                else:
                    for item in eq_raw:
                        info = analyze_equipment(item)
                        if info:
                            bai_obj["equipment"].append(info)
                            eff_str = " | ".join(info['effects'][:2])
                            gem_icon = "💎" if info['has_gem'] else ""
                            print(f"      🔹 {info['slot_name']:<10} ({info['rarity_name']}) {gem_icon} -> {eff_str}")
                
                extracted_data["bailiffs"].append(bai_obj)

        if not extracted_data["commanders"] and not extracted_data["bailiffs"]:
            return None
            
        return extracted_data

    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")
        return None

# --- 4. SALVATAGGIO E AVVIO ---

def save_processed_data(data):
    base_dir = "processed_data"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"inventario_gge_{timestamp}.json"
    filepath = os.path.join(base_dir, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n💾 File JSON salvato con successo: {filepath}")
    except Exception as e:
        print(f"❌ Errore nel salvataggio del file: {e}")

def get_latest_file():
    base_dir = "captured_data/reassembled"
    if not os.path.exists(base_dir): return None
    files = glob.glob(os.path.join(base_dir, "*.json"))
    return max(files, key=os.path.getctime) if files else None

if __name__ == "__main__":
    latest_file = get_latest_file()
    
    if latest_file:
        print(f"📂 Lettura file: {latest_file}")
        all_data = []
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Gestione file con messaggi multipli o singolo oggetto
            if isinstance(content, list):
                print(f"ℹ️  Il file contiene {len(content)} messaggi.")
                for msg in content:
                    # Prova a processare il payload, altrimenti il messaggio intero
                    res = process_game_data(msg.get('payload', msg))
                    if res: all_data.append(res)
            else:
                res = process_game_data(content)
                if res: all_data.append(res)
            
            if all_data:
                save_processed_data(all_data)
            else:
                print("\n⚠️ Nessun dato Comandante/Castellano trovato nel file.")

        except Exception as e:
            print(f"❌ Errore critico: {e}")
    else:
        print("❌ Nessun file JSON trovato nella cartella 'captured_data/reassembled'.")