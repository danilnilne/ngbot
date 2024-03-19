import yaml
import time
import os
import requests
from commands import Commands
import logging

# create logger
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
console_handler.setFormatter(formatter)
# add ch to logger
logger.addHandler(console_handler)


class ScriptExeption(Exception):
    pass


class Config:
    """Bot config base class """

    def __init__(self, filename):
        """Init config, set attributes """

        config = os.path.dirname(os.path.abspath(__file__)) + "/" + filename
        with open(config, 'r') as config:
            settings = yaml.safe_load(config)

        if not settings:
            raise ScriptExeption("Config file empty or has wrong format")

        for key, value in settings.items():
            setattr(self, key, value)

    def add_setting(self, key, value):
        """ Add attribute to config """
        setattr(self, key, value)


def send_http_request(method, url, **kwargs) -> str:
    """
    :param method: str: Any HTTP methods
    :param url: str: URL to send request
    :param kwargs: Dict[str, any]: Dictonary with additional variables

    Send HTTP request with provided variables. If response status code
    not in range (200...299) HTTP request means as failed.
    """

    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
    except Exception:
        raise

    return response.json()


def tg_get_updates() -> list:
    """
    :param api_url str: Telegram Bot API URL
    :param token str: Telegram Bot API token

    Get all updates from Telegram Bot API with specific token
    """

    url = (f"{config.api_url}{config.token}/getUpdates")
    headers = {"application": "json"}

    json_data = send_http_request("GET", url, headers=headers)

    if (json_data) and (json_data['ok'] is True):
        parse_updates(json_data['result'])
    else:
        raise ScriptExeption("Incorrect response from Telegram Bot API")


def parse_updates(updates):
    """
    :param updates list: List with updates

    Parse each update from the list with updates

    Field lists examples in Update:
    text:       ['message_id', 'from', 'chat', 'date', 'text']
    command:    ['message_id', 'from', 'chat', 'date', 'text', 'entities']
    sticker:    ['message_id', 'from', 'chat', 'date', 'sticker']
    """
    if len(updates) == 0:
        logger.info('No updates to be parsed')
        return

    logger.info('%d updates to be parsed', len(updates))

    for update in updates:
        if "text" in update["message"].keys():
            if update["message"]["text"][0] == "/":
                try:
                    result = Commands(update["message"]["text"][1:])
                    tg_reply_message(update, result.data)
                except Exception as commands_exec_error:
                    raise Exception(commands_exec_error)
            else:
                tg_reply_message(update, "Just a text")
        else:
            tg_reply_message(update, "Cannot recognise a message type")


def tg_reply_message(update, reply_data="Empty"):
    """
    :param update dict: update with all attributes which should be answered

    Reply to message from Telegram Bot by given update
    """
    url = (f"{config.api_url}{config.token}/sendMessage")
    headers = {"application": "json"}
    json = {
        "chat_id": update["message"]["chat"]["id"],
        "text": reply_data,
        "reply_parameters": {
            "message_id": update["message"]["message_id"]
        }
    }

    send_http_request("POST", url, headers=headers, json=json)
    tg_resolve_update(update)


def tg_resolve_update(update):
    """
    :param update dict: update which should be marked as resolved

    Mark update as resolved in Telegram Bot API by update_id.
    This update will be deleted from list of updates.
    """
    url = (f"{config.api_url}{config.token}/getUpdates")
    headers = {"application": "json"}
    json = {"offset": update["update_id"] + 1}

    send_http_request("POST", url, headers=headers, json=json)


def tg_send_message(**kwargs):
    """
    :param kwargs: Dict[str, any]: Dictonary with additional variables

    Send to message from Telegram Bot by given variables
    settings = {
        "chat_id": 167625326,
        "text": "1st"
    }
    tg_send_message(**settings)
    """
    if ("chat_id" not in kwargs.keys()) and ("text" not in kwargs.keys()):
        raise ScriptExeption("KeyError: chat_id and text must be provided")

    url = (f"{config.api_url}{config.token}/sendMessage")
    headers = {"application": "json"}
    json = {
        "chat_id": kwargs["chat_id"],
        "text": kwargs["text"]
    }

    send_http_request("POST", url, headers=headers, json=json)


if __name__ == "__main__":

    config: Config = None
    while True:
        if not config:
            try:
                config = Config('config.yml')
            except Exception as init_config_error:
                logger.critical('Unable to init config due to: %s',
                                init_config_error)
        else:
            try:
                tg_get_updates()
            except Exception as work_line_error:
                logger.critical('Unable to get Updates due to: %s',
                                work_line_error)
        time.sleep(3)
