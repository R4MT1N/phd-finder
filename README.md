# PhD Finder

A Telegram bot designed to aggregate announced PhD positions related to computer science field and empower users to follow them through watchlists. Announced positions are collected directly from vacancy pages (or related urls) of universities thorugh web scraping methods.

PhD Finder...

* Checks data sources for new positions in schedule periods
* Leverages source filtering to retrieve the most related positions
* Publishes collected positions to a pre-determined telegram channels
* Allows users to add specific positions to their watchlists
* Allows admin(s) to remove unrelated positions (which could not be fileterd in the collection process)

# Installation
First, copy `example.env`, create `.env` file, and fill the parameters:
```sh
COMPOSE_PROJECT_NAME= # docker-compose project name
##########################
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
##########################
TG_BOT_TOKEN= # Token of your bot which BotFather gave you
TG_CHANNEL_ID= # ID of telegram channel in which the positons are going to publish
ADMIN_TG_ID= # Telegram ID of admin user
```

Then, build the images and run the `docker-compose` as usual:
```sh
docker-compose build # You can skip this if it is your first installation
docker-compose up -d
```
Get the shell access of the `scheduler` container:
```
docker-compose exec scheduler sh
```
Through the shell, execute the `setup` command which creates db tables, insert university-related data, and create the admin user:
```
python main.py setup
```
And it is done! Feel free to make any suggestions; it is a 5-day project which can definitly benefit from more features :)
