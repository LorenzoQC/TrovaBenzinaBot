# TrovaBenzinaBot

[![en](https://img.shields.io/badge/lang-english-blue.svg)](https://github.com/LorenzoQC/TrovaBenzinaBot/blob/main/README.md)

Bot Telegram che permette agli utenti di trovare i distributori di carburante più economici in Italia.

## ✨ Funzionalità

* **Ricerca distributori**: Individua i distributori con i prezzi più bassi per il tipo di carburante selezionato nelle
  vicinanze dell'utente.
* **Geolocalizzazione**: Utilizza la condivisione della posizione di Telegram per identificare rapidamente i
  distributori più vicini.
* **Personalizzazione**: Gli utenti possono selezionare lingua e tipo di carburante preferiti.
* **Statistiche di risparmio**: Mostra statistiche personalizzate sul risparmio ottenuto dall'utente grazie al bot.
* **Interfaccia intuitiva**: Comandi semplici e pulsanti inline per una navigazione immediata.

## 🛠️ Tecnologie utilizzate

* Python 3.12
* Telegram Bot API (`python-telegram-bot[webhooks]==22.2`)
* Framework web: `aiohttp==3.10.11` per la gestione dei webhook
* Driver database: `asyncpg>=0.27.0` per PostgreSQL
* Scheduling: `APScheduler==3.10.4`
* ORM e supporto async: `SQLAlchemy[asyncio]>=2.0.0`
* Operazioni su file: `aiofiles~=24.1.0`


## 🚀 Deployment

Il bot è attualmente deployato su [Railway](https://railway.app) ed è disponibile su Telegram
come [@trovabenzinabot](https://t.me/trovabenzinabot).

## 🗂️ Struttura del progetto

```plaintext
.
├── assets/                  # Risorse statiche del bot
│   ├── config/              # File di configurazione aggiuntiva
│   │   ├── csv/             # File CSV di dati
│   │   └── sql/             # Script SQL di inizializzazione
│   └── images/              # Immagini e icone
├── src/                     # Codice sorgente dell'applicazione
│   └── trovabenzina/
│       ├── api/             # Integrazioni con API esterne (Google Maps, MISE)
│       ├── config/          # Gestione configurazioni e segreti
│       ├── core/            # Avvio del bot e scheduler
│       ├── db/              # Accesso e sincronizzazione database
│       ├── handlers/        # Gestori dei comandi e conversazioni
│       ├── i18n/            # Traduzioni multilingua
│       └── utils/           # Funzioni di utilità e helper
├── requirements.txt         # Dipendenze del progetto
├── Dockerfile               # Configurazione Docker per il deployment
└── README.md                # Documentazione del progetto
```

## 📌 Comandi del bot

* `/start`: Avvia la configurazione del profilo utente.
* `/find`: Cerca i distributori di carburante più economici in base alla posizione attuale.
* `/profile`: Visualizza o modifica le preferenze del profilo (lingua, tipo di carburante).
* `/statistics`: Visualizza le statistiche di risparmio.
* `/help`: Mostra informazioni di aiuto e comandi disponibili.

## 🤝 Contribuire

Le pull request sono benvenute. Per modifiche importanti, apri prima un issue per discutere le modifiche.

## 📄 Licenza

Questo progetto è rilasciato con licenza MIT. Consulta il file `LICENSE` per i dettagli.
