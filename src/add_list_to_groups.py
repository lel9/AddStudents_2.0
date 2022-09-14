import argparse

from lib.helpers import *
from lib.logic import add_one_to_groups_by_login

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Параметры запуска:')
    parser.add_argument('group', type=str, help='Название группы в Redmine')
    parser.add_argument('-i', '--fin', type=str, default='./logins.txt',
                        help='Полный путь к входному файлу с логинами (по-умолчанию ./logins.txt)')
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

    error = try_open(ns.fin)
    if error:
        print('Ошибка открытия файла ' + ns.fin + ':')
        process_errors([error])
        exit()

    error, redmine = get_redmine(config)
    if error:
        print('Ошибка подключения к Redmine:')
        process_errors([error])
        exit()

    with open(ns.fin, 'r', encoding="UTF-8") as f:
        logins = [x.strip() for x in f.readlines() if len(x.strip()) > 0]
        for login in logins:
            error = add_one_to_groups_by_login(login, ns.group, redmine)
            if error:
                print('Ошибка добавления студента ' + login + ' в группу')
                process_errors([error])
            else:
                print('Студент ' + login + ' успешно добавлен в группу')
