# Campfire

A utility discord bot created with the goal of enhancing the list of available features for community server managers.

## Setup

This bot depends on the python module `hikari`. A list of supported python versions can be found here https://github.com/hikari-py/hikari

Upon cloning the repository, you will need to create a `.env` file to set your environment variables and install the project dependencies. 

### Python Dependencies

You may wish to create a virtual environment prior to installing dependencies. Dependencies should be installed from `requirements.txt` using `pip install -r requirements.txt`

### Environment Variables

The .env file needs to contain the following variables.

```
TOKEN=...           # Discord Application Token
DATABASE_URI=...    # MongoDB Connection String
OPENAI_KEY=...      # OpenAI Secret Key
```

Discord application tokens can be obtained at https://discord.com/developers/
OpenAI secret keys can be obtained at https://platform.openai.com/account/api-keys

## Running the bot

To run the bot, simply run the `bot.py` file in the `bot` directory. Please note this should only be done after following the setup instructions listed above.

```bash
$ python3 -O bot.py
```

## Planned Features

- [x] Tags
- [ ] Custom Lobbies (Undergoing heavy reworks)
- [x] Profanity Filter
- [ ] Server Stats
- [ ] Birthdays

### Old

- [ ] Reputation    (Was previously implemented but has been temporarily removed due to poor implementation)
