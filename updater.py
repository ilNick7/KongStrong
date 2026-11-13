import os
import io
import json
import hashlib
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CAMPIONATI = {
    "Serie A": "https://football-data.co.uk",
    "Premier League": "https://football-data.co.uk",
    "La Liga": "https://football-data.co.uk",
    "Bundesliga": "https://football-data.co.uk",
    "Ligue 1": "https://football-data.co.uk"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def invia_notifica(testo):
    if not TOKEN or not CHAT_ID:
        print("Mancano TELEGRAM_TOKEN o TELEGRAM_CHAT_ID")
        return
    url = f"https://telegram.org{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "HTML"})

def calcola_statistiche():
    risultati = {}
    
    for nome_lega, url in CAMPIONATI.items():
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        
        # Controllo di sicurezza: verifica che sia davvero un CSV e non una pagina HTML
        if "<html" in resp.text.lower()[:300]:
            raise ValueError(f"Il server ha restituito HTML invece del CSV per {nome_lega}")
            
        df = pd.read_csv(io.StringIO(resp.text), on_bad_lines="skip")
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "HS", "AS"])
        
        squadre = sorted(df["HomeTeam"].unique())
        risultati[nome_lega] = {}
        
        for sq in squadre:
            casa = df[df["HomeTeam"] == sq]
            trasf = df[df["AwayTeam"] == sq]
            partite = len(casa) + len(trasf)
            
            if partite == 0:
                continue
                
            tiri_tot = casa["HS"].sum() + trasf["AS"].sum()
            tiri_porta = casa["HST"].sum() + trasf["AST"].sum()
            corner = casa["HC"].sum() + trasf["AC"].sum()
            falli_fatti = casa["HF"].sum() + trasf["AF"].sum()
            falli_subiti = casa["AF"].sum() + trasf["HF"].sum()
            cartellini = (casa["HY"].sum() + casa["HR"].sum() + 
                          trasf["AY"].sum() + trasf["AR"].sum())
            
            risultati[nome_lega][sq] = {
                "partite": int(partite),
                "tiri_totali": round(float(tiri_tot / partite), 2),
                "tiri_porta": round(float(tiri_porta / partite), 2),
                "corner": round(float(corner / partite), 2),
                "falli_fatti": round(float(falli_fatti / partite), 2),
                "falli_subiti": round(float(falli_subiti / partite), 2),
                "cartellini": round(float(cartellini / partite), 2)
            }
            
    return risultati

def main():
    nuovi_dati = calcola_statistiche()
    nuovo_hash = hashlib.md5(json.dumps(nuovi_dati, sort_keys=True).encode()).hexdigest()
    
    vecchio_hash = ""
    if os.path.exists("stats.json"):
        with open("stats.json", "r", encoding="utf-8") as f:
            vecchio_file = json.load(f)
            vecchio_hash = vecchio_file.get("hash", "")
            
    if nuovo_hash != vecchio_hash:
        adesso = datetime.now().strftime("%d/%m/%Y alle %H:%M")
        output = {
            "ultimo_aggiornamento": adesso,
            "hash": nuovo_hash,
            "dati": nuovi_dati
        }
        with open("stats.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        invia_notifica(
            f"📊 <b>Statistiche Aggiornate!</b>\n\n"
            f"I dati dei Top 5 campionati europei sono stati aggiornati.\n"
            f"🕒 <b>Data rilevamento:</b> {adesso}"
        )
        print("Statistiche aggiornate e notifica inviata.")
    else:
        print("Nessuna modifica nei dati.")

if __name__ == "__main__":
    main()
