# TrovaBenzinaBot

[![en](https://img.shields.io/badge/lang-english-blue.svg)](https://github.com/LorenzoQC/TrovaBenzinaBot/blob/main/README.md)

Bot Telegram che permette agli utenti di trovare i distributori di carburante più economici in Italia.

## 🚀 Funzionalità

* **Ricerca Distributori**: Individua i distributori con i prezzi più bassi per il tipo di carburante selezionato nelle
  vicinanze dell'utente.
* **Geolocalizzazione**: Utilizza la condivisione della posizione di Telegram per identificare rapidamente i
  distributori più vicini.
* **Personalizzazione**: Gli utenti possono selezionare lingua, tipo di carburante e tipo di servizio preferiti.
* **Interfaccia Intuitiva**: Comandi semplici e pulsanti inline per una navigazione immediata.

## 🛠️ Tecnologie Utilizzate

* Python 3.12
* Telegram Bot API (`python-telegram-bot[webhooks] v22.2`)
* Web framework: `aiohttp` per la gestione dei webhook
* Database PostgreSQL (`asyncpg`)
* APScheduler per attività periodiche

## 📦 Requisiti

I pacchetti necessari sono elencati nel file `requirements.txt`. Installali con:

```bash
pip install -r requirements.txt
```

## 🚀 Deployment

Il bot è attualmente deployato su [Railway](https://railway.app) ed è disponibile su Telegram
come [@trovabenzinabot](https://t.me/trovabenzinabot).

## 🌐 Configurazione Variabili d'Ambiente

Imposta le seguenti variabili d'ambiente:

* `TELEGRAM_TOKEN`: Token del bot Telegram
* `DATABASE_URL`: URL di connessione a PostgreSQL
* `GOOGLE_MAPS_API_KEY`: API Key per Google Maps Geocoding

## 🔧 Struttura del Progetto

```plaintext
.
├── assets/            # Immagini e risorse multimediali del bot
├── src/               # Codice sorgente dell'applicazione
│   └── trovabenzina/
│       ├── bot/       # Inizializzazione del bot e configurazione scheduler
│       ├── config/    # Gestione configurazioni e segreti
│       ├── core/      # Moduli core: interazioni con API e database
│       ├── handlers/  # Gestori dei comandi del bot
│       ├── i18n/      # File di traduzione per le lingue supportate
│       └── utils/     # Funzioni di utilità e helper
├── requirements.txt   # Dipendenze del progetto
├── Dockerfile         # Configurazione Docker per il deployment
└── README.md          # Documentazione del progetto
```

## 📌 Comandi Principali del Bot

* `/start`: Avvia la configurazione del profilo utente.
* `/find`: Trova il distributore di carburante più economico in base alla posizione attuale.
* `/preferences`: Modifica preferenze di lingua, carburante e tipo di servizio.

## 🤝 Contribuire

Le pull request sono benvenute. Per modifiche importanti, apri prima un issue per discutere le modifiche.

## 📄 Licenza

Questo progetto è rilasciato con licenza MIT. Consulta il file `LICENSE` per i dettagli.
