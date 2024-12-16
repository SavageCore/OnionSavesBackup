import json
import os

CONFIG_FILE = os.path.expanduser("~/OnionSavesBackup/config.json")


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
        with open(CONFIG_FILE, "r") as f:
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
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
