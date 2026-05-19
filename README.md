# real-time-data-engineering

Stack Docker incluse:
- Kafka en mode KRaft
- Redis pour le bus de sante Socket.IO
- MongoDB pour la persistance des trades
- 3 workers consommateurs Kafka
- Socket.IO pour le temps reel
- Stream Binance BTC en temps reel
- Dashboard web pour la sante de la pipeline

Lancement:

```bash
docker compose up --build
```

Notes:
- Le service `binance-stream` lit le websocket Binance puis publie chaque trade dans le topic Kafka `binance.trades`.
- Les trois workers lisent le meme topic Kafka avec le consumer group `binance-trade-workers`.
- Les trades consommes sont inseres dans MongoDB dans la collection `market_data.binance_trades`.
- Le serveur Socket.IO ecoute sur le port `8000` et sert au dashboard de sante, pas au stream Binance.
- Le stream Binance se reconnecte tout seul si la socket coupe ou devient inactive.
- Le moniteur d'orchestration publie les snapshots d'etat.
- Le dashboard est accessible sur `http://localhost:3000`.
