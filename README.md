# Campfire

A community focused utility discord bot created with the goal of enhancing the list of available features for server managers.

## Setup

This bot depends on the python module `hikari`. A list of supported python versions can be found here https://github.com/hikari-py/hikari

Upon cloning the repository, you will need to create a `.env` file to set your environment variables and install the project dependencies. 

### Python Dependencies

You may wish to create a virtual environment prior to installing dependencies. Dependencies should be installed from `requirements.txt` using `pip install -r requirements.txt`

### Environment Variables

The .env file should simply contain the application token to be used by the bot.

```
TOKEN=... # Discord Application Token
```

Application tokens can be obtained at https://discord.com/developers/

## Running the bot

To run the bot, simply run `campfire/bot.py`. Please note this should only be done after following the setup instructions listed above.

```bash
$ python3 bot.py
```

## Planned Features

- [x] Tags
- [x] Custom Lobbies
- [ ] Server Stats
- [ ] Birthdays

### Old

- [ ] Reputation    (Was previously implemented but has been temporarily removed due to poor implementation)
