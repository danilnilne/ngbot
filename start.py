import os
import sys
import yaml
import time
import signal
import logging
import requests
import multiprocessing
from commands import Commands


# Create logger
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.DEBUG)

# Create formatter
# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s')

# Add formatter to ch
console_handler.setFormatter(formatter)

# Add ch to logger
logger.addHandler(console_handler)


class ScriptException(Exception):
    """Base class for script Exception"""
    pass


class Config:
    """Bot config base class """

    def __init__(self, filename):
        """Init config, set attributes """

        config_filename = os.path.dirname(os.path.abspath(__file__)) + "/" + filename
        with open(config_filename, 'r') as file:
            settings = yaml.safe_load(file)

        if not settings:
            raise ScriptException("Config file empty or has wrong format")

        for key, value in settings.items():
            setattr(self, key, value)

    def add_setting(self, key, value):
        """ Add attribute to config """
        setattr(self, key, value)


class Updates:
    """ TG updates base class """

    def __init__(self) -> list:
        """ Get updates from Telegram API """
        self.entries = tg_get_updates()
        for entry in self.entries:
            entry.update({'is_new': True,
                          'in_progress': False,
                          'is_done': False})
            logger.debug(
                '%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s',
                __name__, entry["update_id"],entry["is_new"], entry["in_progress"], entry["is_done"])
            
        
    def sync_updates_from_api(self) -> list:
        """
        Get updates from Telegram API and compare with self.entries
        Duplicate entries should be skipped from updating
        """
        old_update = len(self.entries)
        new_updates = 0

        exist_update_ids = []
        for entry in self.entries:
            exist_update_ids.append(entry["update_id"])
            logger.debug('%s: update [%s]', __name__, entry["update_id"])

        for entry in tg_get_updates():
            if entry["update_id"] not in exist_update_ids:
                entry.update({'is_new': True,
                              'in_progress': False,
                              'is_done': False})
                self.entries.append(entry)
                new_updates = new_updates + 1
                logger.debug(
                '%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s',
                __name__, entry["update_id"],entry["is_new"], entry["in_progress"], entry["is_done"])
            else:
                logger.info('%s: duplicates for [%s]',
                            __name__, entry["update_id"])
        logger.debug('%s: updates exist: %d, comes: %d',
                     __name__, old_update, new_updates)


    def delete_entry(self, update_id) -> None:
        self.entries = [d for d in self.entries if d.get("update_id") != update_id]

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
        return json_data['result']
    else:
        raise ScriptException("Incorrect response from Telegram Bot API")


def handle_update(update) -> str:
    """
    :param update dict: Update dictonary with k/v

    Parse update

    Fields list examples in Update:
    text:       ['message_id', 'from', 'chat', 'date', 'text']
    command:    ['message_id', 'from', 'chat', 'date', 'text', 'entities']
    sticker:    ['message_id', 'from', 'chat', 'date', 'sticker']
    """
    proc_name = multiprocessing.current_process().name
    proc_id = multiprocessing.current_process().pid
    logger.debug('%s: update [%s] | %s with %s pid',
                __name__, update["update_id"], proc_name, proc_id)
    
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
    
    update.update({'is_done': True})
    logger.debug('%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s',
                 __name__, update["update_id"], update["is_new"], update["in_progress"], update["is_done"])
    return update


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
    logger.debug('%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s',
                 __name__, update["update_id"], update["is_new"], update["in_progress"], update["is_done"])

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
    logger.debug('%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s',
                 __name__, update["update_id"], update["is_new"], update["in_progress"], update["is_done"])

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
        raise ScriptException("KeyError: chat_id and text must be provided")

    url = (f"{config.api_url}{config.token}/sendMessage")
    headers = {"application": "json"}
    json = {
        "chat_id": kwargs["chat_id"],
        "text": kwargs["text"]
    }

    send_http_request("POST", url, headers=headers, json=json)


def init_worker(global_config):
    """
    Эта функция выполнится в КАЖДОМ процессе пула при его создании.
    Она записывает переданный конфиг в глобальную переменную ЭТОГО процесса.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    global config
    config = global_config
    logger.debug('%s: config: %s', __name__, config)


def pool_notifier(update):
    logger.debug('%s: update [%s] to resolve', __name__, update["update_id"])
    tg_resolve_update(update)
    updates.delete_entry(update["update_id"])

if __name__ == "__main__":
    config: Config = None
    updates: Updates = None

    if not config:
        try:
            config = Config('config.yml')
            logger.info('%s: config file initilized: %s',
                        __name__, isinstance(config, Config))
        except Exception as init_config_error:
            logger.critical('%s: unable to init config due to: %s',
                            __name__, init_config_error)
            sys.exit(1)

    if not updates:
        try:
            updates = Updates()
            logger.info('%s: %d update(s) to be parsed',
                        __name__, len(updates.entries))
        except Exception as work_line_error:
            logger.critical('%s: unable to init Updates class due to: %s',
                            __name__, work_line_error)
            exit()

    pool = multiprocessing.Pool(initargs=(config,), initializer=init_worker)
    try:
        while True:
            logger.info('%s: %d update(s) to be parsed',
                        __name__, len(updates.entries))
            for entry in updates.entries:
                if entry["is_new"] and not entry["in_progress"]:
                    pool.apply_async(handle_update,
                                    args=(entry,),
                                    callback=pool_notifier)
                    logger.debug('%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s sent to Pool()',
                                 __name__, entry["update_id"], entry["is_new"], entry["in_progress"], entry["is_done"])
                    entry.update({'is_new': False,
                                  'in_progress': True,
                                  'is_done': False})
                    logger.debug('%s: update [%s] | is_new: %s | in_progress: %s | is_done: %s changed.',
                                 __name__, entry["update_id"], entry["is_new"], entry["in_progress"], entry["is_done"])
            updates.sync_updates_from_api()
            logger.info('%s: === all update(s) handled. Waiting for %s sec... ===',
                        __name__, config.api_heartbeat)
            time.sleep(config.api_heartbeat)
    except KeyboardInterrupt:
        logger.critical('%s: Programm is terminating', __name__)
    finally:
        pool.terminate()
        pool.join()
    logger.info('Exit, Bye!')