# Campfire

A utility discord bot created with the goal of enhancing the list of features available to users who manage discord servers.

This version of the Campfire discord bot written using the hikari and hikari-lightbulb libraries as opposed to the discord.py library used in the original.

The project was formally revitalized in November 2021 and is still in development as a side project for the time being.

## Usage

Python 3.8, 3.9 and 3.10 are currently the only supported versions.

Upon cloning the repository, you will need to create a `config.ini` file and install the project dependencies. Dependencies should be installed from `requirements.txt` using `pip install -r requirements.txt`

### Config File

The config file will have two sections, `[PRODUCTION]` and `[DEVELOPMENT]`.

If you intend on running the bot without modification, you only need to implement the production section.

```ini
[PRODUCTION]
TOKEN=... # Production Discord Application Token
DATABASE_URI=... # MongoDB Production Database URL

[DEVELOPMENT]
TOKEN=... # Development Discord Application Token
GUILD=... # Development Discord Server ID
DATABASE_URI=... # MongoDB Development Database URL
```

Application tokens can be obtained at https://discord.com/developers/

### Running the bot

Below are instructions for running your bot depending on whether you want to run your production or development application. This should only be done after installing dependencies and creating your `config.ini` file.

```bash
# Production
python3 bot.py

# Development
python3 bot.py -d
```

## Planned Features

The application will be moved to production and released publicly once 3 features have been implemented to an acceptable degree of completion.

- [x] Tags
- [x] Custom Lobbies
- [ ] Reputation
- [ ] Server Stats
- [ ] Birthdays
