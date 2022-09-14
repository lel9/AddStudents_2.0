import argparse

from src.lib.helpers import *
from src.lib.logic import delete_user

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Параметры запуска:')
    parser.add_argument('-i', '--fin', type=str, default='../logins.txt',
                        help='Полный путь к входному файлу с логинами (по-умолчанию ../logins.txt)')

    ns = parser.parse_args()
    print(ns)

    # читаем конфиги
    error, config = read_config('../settings.ini')
    if error:
        print('Ошибка чтения настроечного файла settings.ini!')
        process_errors([error])
        exit()
    else:
        print('Настроечный файл успешно прочитан...')

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

    error, gitlab = get_gitlab(config)
    if error:
        print('Ошибка подключения к Gitlab:')
        process_errors([error])
        exit()

    with open(ns.fin, 'r', encoding="UTF-8") as f:
        logins = [x.strip() for x in f.readlines() if len(x.strip()) > 0]
        for login in logins:
            errors = delete_user(login, redmine, gitlab)
            if len(errors) > 0:
                print("Ошибки удаления студента " + login + ':')
                process_errors(errors)
            else:
                print('Студент ' + login + ' успешно удален везде')

