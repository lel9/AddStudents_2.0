import codecs
import configparser
import random
import smtplib
import string
from getpass import getpass

import gitlab
from redminelib import Redmine


def process_warnings(warnings):
    for w in warnings:
        print(w)


def process_errors(errors):
    for e in errors:
        print(e)


def print_student(snum, student):
    print(snum + ' = { ', end='')
    for k, v in student.items():
        print(str(k) + ': ' + str(v), end=', ')
    print(' }')


def exc_to_str(e):
    return str(type(e)) + ': ' + str(e)


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
        return exc_to_str(e)
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

        if 'Email' not in config:
            return 'Настройки Email не найдены', None
        if 'from' not in config['Email']:
            return 'Настройка from не найдена', None
        if 'host' not in config['Email']:
            return 'Настройка host не найдена', None

    except Exception as e:
        return exc_to_str(e), None
    return None, config


def get_redmine(config):
    try:
        return None, Redmine(config['Redmine']['redmine_host'],
                          key = config['Redmine']['redmine_key'])
    except Exception as e:
        return exc_to_str(e), None


def get_gitlab(config):
    try:
        # private token or personal token authentication (self-hosted GitLab instance)
        gl = gitlab.Gitlab(url=config['Gitlab']['gitlab_host'],
                           private_token=config['Gitlab']['gitlab_token'])

        # make an API request to create the gl.user object. This is not required but may be useful
        # to validate your token authentication. Note that this will not work with job tokens.
        gl.auth()
    except Exception as e:
        return exc_to_str(e), None
    return None, gl


def get_email_data(config, fmail_template):
    warnings = []
    error = try_open(fmail_template)
    if error:
        return error, warnings, None

    email_data = dict()
    with open(fmail_template, 'r', encoding="UTF-8") as f:
        email_data['subject'] = f.readline().strip()
        if len(email_data['subject']) == 0:
            warnings.append('Не указана тема отправляемого письма')

        text = f.readlines()
        i = 0
        while i < len(text) and len(text[i].strip()) == 0:
            i += 1
        if i == len(text):
            error = 'Не указан текст отправляемого письма'
            return error, warnings, None

        email_data['template'] = ''.join(text[i:])
        email_data['from'] = config['Email']['from']

        try:
            server = smtplib.SMTP(config['Email']['host'])
            passw = getpass("Введите пароль от п/я " + email_data['from'] + ': ')
            server.login(email_data['from'], passw)
            email_data['smtp_server'] = server
        except Exception as e:
            return exc_to_str(e), warnings, None
    return None, warnings, email_data


def quit_server(email_data):
    email_data['smtp_server'].quit()