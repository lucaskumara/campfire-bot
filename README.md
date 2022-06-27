# Campfire

A utility discord bot created with the goal of enhancing the list of features available to users who manage discord servers.

This version of the Campfire discord bot written using the hikari and hikari-lightbulb libraries as opposed to the discord.py library used in the original.

The project was formally revitalized in November 2021 and is still in development as a side project for the time being.

## Usage

Python 3.8, 3.9 and 3.10 are currently the only supported versions.

Upon cloning the repository, you will need to create a `config.ini` file and install the project dependencies. Dependencies should be installed from `requirements.txt` using `pip install -r requirements.txt`

### Config File

The config file can have two sections, `[BOT]` and `[OPTIONAL]`.

The `[BOT]` section contains values that are critical to the operation of the application. The `[OPTIONAL]` section contains additional values that are not required for operation but can modify the way the application is run.

```ini
[BOT]
TOKEN=... # Discord Application Token
DATABASE_URI=... # MongoDB Database URL

[OPTIONAL]
GUILDS=[..., ...] # Development Discord Server IDs
```

Application tokens can be obtained at https://discord.com/developers/

### Running the bot

To run the bot, simply run the `bot.py` file. Please note this should only be done after installing dependencies and creating your `config.ini` file.

```bash
$ python3 bot.py
```

## Planned Features

The application will be moved to production and released publicly once 3 features have been implemented to an acceptable degree of completion.

- [x] Tags
- [x] Custom Lobbies
- [x] Reputation
- [ ] Server Stats
- [ ] Birthdays
