import argparse

from lib.helpers import *
from lib.logic import change_passw_user

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Параметры запуска:')
    parser.add_argument('login', help='Логин')
    parser.add_argument('-m', '--fmail_template', type=str, default='./email2.txt',
                        help='Полный путь к файлу с шаблоном и темой письма (по-умолчанию ./email2.txt)')
    parser.add_argument('-s', '--fsettings', type=str, default='./settings.ini',
                        help='Полный путь к файлу с настройками (по-умолчанию ./settings.ini)')

    ns = parser.parse_args()
    print(ns)

    # читаем конфиги
    error, config = read_config(ns.fsettings)
    if error:
        print('Ошибка чтения настроечного файла settings.ini:')
        process_errors([error])
        exit()

    error, redmine = get_redmine(config)
    if error:
        print('Ошибка подключения к Redmine:')
        process_errors([error])
        exit()

    error, gitlab = get_gitlab(config)
    if error:
        print('Ошибка подключения к Gitlab:')
        process_errors([error])
        exit()

    error, warnings, email_data = get_email_data(config, ns.fmail_template)
    if error:
        print('Ошибка подключения к почте или чтения шаблона письма:')
        process_errors([error])
        exit()
    if len(warnings) > 0:
        print('Предупреждения при подключении к почте или чтении шаблона письма:')
        process_warnings(warnings)

    errors = change_passw_user(ns.login, redmine, gitlab, email_data)
    if len(errors) > 0:
        print("Ошибки смены пароля для студента " + ns.login + ':')
        process_errors(errors)
    else:
        print('Для студента ' + ns.login + ' успешно изменен пароль')
