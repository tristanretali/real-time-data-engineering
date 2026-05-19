# real-time-data-engineering

Stack Docker incluse:
- Kafka + Zookeeper
- Redis comme broker Celery
- 3 workers Celery distincts
- Socket.IO pour le temps reel
- Stream Binance BTC en temps reel
- Dashboard web pour la sante de la pipeline

Lancement:

```bash
docker compose up --build
```

Notes:
- Celery ne consomme pas Kafka directement comme broker standard, donc Kafka est fourni comme bus d'evenements et Redis sert de broker Celery.
- Les workers utilisent la tache `app.tasks.process_message`.
- Le serveur Socket.IO ecoute sur le port `8000`.
- Le consumer Binance publie seulement des heartbeats de sante.
- Le moniteur d'orchestration publie les snapshots d'etat.
- Le dashboard est accessible sur `http://localhost:3000`.
