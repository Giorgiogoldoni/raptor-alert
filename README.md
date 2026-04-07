# 🦅 RAPTOR Alert

Analisi automatica di 700 ETF con segnali LONG / EARLY / WATCH / ROSSO+

## Come funziona

```
data/etf.json  ←  aggiornato ogni ora da GitHub Actions (fetch_data.py)
index.html     ←  legge il JSON e mostra la tabella con i segnali
```

## Struttura

```
raptor-alert/
├── index.html                        ← pagina principale
├── fetch_data.py                     ← script Python che scarica i dati
├── data/
│   └── etf.json                      ← dati pre-calcolati (auto-aggiornati)
└── .github/
    └── workflows/
        └── update.yml                ← GitHub Actions: ogni ora
```

## URL live

`https://giorgiogoldoni.github.io/raptor-alert/`

## Dati

La pagina funziona in tre modalità (in ordine di priorità):
1. **JSON server** — legge `data/etf.json` aggiornato ogni ora (veloce, nessun CORS)
2. **Live Yahoo Finance** — premi CALCOLA per analisi in tempo reale
3. **Cache locale** — ricarica l'ultima analisi salvata nel browser
