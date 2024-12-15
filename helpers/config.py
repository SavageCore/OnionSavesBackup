import json


def read_config():
    """
    Read the configuration file.

    Returns
    -------
    dict
        The configuration file as a dictionary.
    False
        If the configuration file does not exist.
    """
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        return False


def create_config():
    """
    Create a new configuration file.
    """
    # Create the configuration file
    config = {}
    save_config(config)
    # Clear the screen
    print("\033[H\033[J")


def save_config(config):
    """
    Save the configuration file.

    Parameters
    ----------
    config : dict
        The configuration file as a dictionary.
    """
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
