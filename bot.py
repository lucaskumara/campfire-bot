import lightbulb
import argparse
import configparser


class Campfire(lightbulb.BotApp):
    '''A class to represent an instance of the Campfire bot application.

    Attributes:
        database_client (AsyncIOMotorClient): The client connection to the
            MongoDB database. (Not set upon instantiation)
        database (AsyncIOMotorDatabase): The database where all application
            data will be stored. (Not set upon instantiation)
    '''

    def __init__(self, token: str, guilds: tuple) -> None:
        '''Initializes an instance of Campfire.

        Calls the .__init__(...) method of the superclass and passes in all
        required values.

        Arguments:
            token: The application token.
            guilds: Tuple of guild ids to register application commands to.
        '''
        super().__init__(token=token, default_enabled_guilds=guilds)


parser = argparse.ArgumentParser()
parser.add_argument('-d', action='store_true')

config = configparser.ConfigParser()
config.read('config.ini')

if __name__ == '__main__':
    args = parser.parse_args()

    if args.d:
        token = config.get('DEVELOPMENT', 'TOKEN')
        guilds = (config.getint('DEVELOPMENT', 'GUILD'))
    else:
        token = config.get('PRODUCTION', 'TOKEN')
        guilds = ()

    bot = Campfire(token, guilds)
    bot.load_extensions_from('./extensions')
    bot.run()
