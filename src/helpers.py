import codecs
import configparser
import random
import string
import traceback

import gitlab
from redminelib import Redmine


def random_pass(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))


def add_zero(string):
    if len(string) < 2:
        return '0'+string
    return string


def try_open(fpath):
    try:
        with open(fpath, 'r', encoding='UTF-8'):
            pass
    except Exception as e:
        return e
    return None


def read_config(path):
    try:
        # загружаем настройки
        config = configparser.ConfigParser()  # создаём объекта парсера
        config.readfp(codecs.open(path, "r", "utf8")) # читаем конфиг

        if 'Redmine' not in config:
            return 'Настройки Redmine не найдены', None
        if 'redmine_host' not in config['Redmine']:
            return 'Настройка redmine_host не найдена', None
        if 'redmine_key' not in config['Redmine']:
            return 'Настройка redmine_key не найдена', None

        if 'Gitlab' not in config:
            return 'Настройки Gitlab не найдены', None
        if 'gitlab_host' not in config['Gitlab']:
            return 'Настройка gitlab_host не найдена', None
        if 'gitlab_token' not in config['Gitlab']:
            return 'Настройка gitlab_token не найдена', None

    except Exception as e:
        return e, None
    return None, config


def get_redmine(config):
    try:
        return None, Redmine(config['Redmine']['redmine_host'],
                          key = config['Redmine']['redmine_key'])
    except Exception as e:
        return e, None


def exc_to_str(e):
    return str(type(e)) + str(e.args) + ': ' + str(e)


def get_gitlab(config):
    try:
        # private token or personal token authentication (self-hosted GitLab instance)
        gl = gitlab.Gitlab(url=config['Gitlab']['gitlab_host'],
                           private_token=config['Gitlab']['gitlab_token'])

        # make an API request to create the gl.user object. This is not required but may be useful
        # to validate your token authentication. Note that this will not work with job tokens.
        gl.auth()
    except Exception as e:
        return e, None
    return None, gl