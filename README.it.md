# TrovaBenzinaBot

[![en](https://img.shields.io/badge/lang-english-blue.svg)](https://github.com/LorenzoQC/TrovaBenzinaBot/blob/main/README.md)

Telegram bot that allows users to find the cheapest fuel stations nearby in Italy.

## 🚀 Features

* **Fuel Station Search**: Finds fuel stations offering the lowest prices for the selected fuel type near the user's
  location.
* **Geolocation**: Uses Telegram's location sharing to quickly pinpoint nearby fuel stations.
* **Personalization**: Users can select preferred language, fuel type, and service type.
* **Intuitive Interface**: Simple commands and inline buttons for immediate navigation.

## 🛠️ Technologies Used

* Python 3.12
* Telegram Bot API (`python-telegram-bot[webhooks] v22.2`)
* Web framework: `aiohttp` for handling webhooks
* PostgreSQL database (`asyncpg`)
* APScheduler for periodic tasks

## 📦 Requirements

Required packages are listed in the `requirements.txt` file. Install them using:

```bash
pip install -r requirements.txt
```

## 🚀 Deployment

The bot is currently deployed on [Railway](https://railway.app) and is live on Telegram
as [@trovabenzinabot](https://t.me/trovabenzinabot).

## 🌐 Environment Variables Configuration

Set the following environment variables:

* `TELEGRAM_TOKEN`: Telegram bot token
* `DATABASE_URL`: PostgreSQL connection URL
* `GOOGLE_MAPS_API_KEY`: API Key for Google Maps Geocoding

## 🔧 Project Structure

```plaintext
.
├── assets/       # Images and media assets used by the bot
├── src/          # Source code of the application
│   └── trovabenzina/
│       ├── bot/        # Bot initialization and scheduler setup
│       ├── config/     # Configuration and secret management
│       ├── core/       # Core modules: API and database interactions
│       ├── handlers/   # Handlers for various bot commands
│       ├── i18n/       # Translation files for supported languages
│       └── utils/      # Utility functions and helpers
├── requirements.txt  # Project dependencies
└── Dockerfile        # Docker configuration for containerized deployment
```

## 📌 Main Bot Commands

* `/start`: Start user profile configuration.
* `/find`: Find the cheapest fuel station based on current location.
* `/preferences`: Edit language, fuel, and service preferences.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
