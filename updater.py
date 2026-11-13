import os
import json
import hashlib
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# URL dei CSV della stagione 2026/2027 (codice 2627) su Football-Data.co.uk
CAMPIONATI = {
    "Serie A": "https://football-data.co.uk",
    "Premier League": "https://football-data.co.uk",
    "La Liga": "https://football-data.co.uk",
    "Bundesliga": "https://football-data.co.uk",
    "Ligue 1": "https://football-data.co.uk"
}

def invia_notifica(testo):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": testo, "parse_mode": "HTML"})

def calcola_statistiche():
    risultati = {}
    
    for nome_lega, url in CAMPIONATI.items():
        df = pd.read_csv(url)
        # Rimuove eventuali righe vuote o partite non ancora giocate
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
                "tiri_totali": round(tiri_tot / partite, 2),
                "tiri_porta": round(tiri_porta / partite, 2),
                "corner": round(corner / partite, 2),
                "falli_fatti": round(falli_fatti / partite, 2),
                "falli_subiti": round(falli_subiti / partite, 2),
                "cartellini": round(cartellini / partite, 2)
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
    else:
        print("Nessuna modifica nei dati.")

if __name__ == "__main__":
    main()
