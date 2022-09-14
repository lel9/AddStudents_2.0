import argparse

from lib.helpers import *
from lib.minput import read_student_cmd
from lib.logic import one_gre_transaction, add_one_to_groups

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Параметры запуска:')

    parser.add_argument('name', type=str, help='ФИО в кавычках')
    parser.add_argument('email', type=str, help='почта')
    parser.add_argument('-u', '--eu_id', type=str, default='-1', help='ID в ЭУ')
    parser.add_argument('-g', '--groups', type=str, default='[]',
                        help='Список групп в [] и кавычках, разделитель запятая')
    parser.add_argument('-m', '--fmail_template', type=str, default='./email1.txt',
                        help='Полный путь к файлу с шаблоном и темой письма (по-умолчанию ./email1.txt)')
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

    errors, warnings, student = read_student_cmd(ns)
    if len(errors) > 0:
        print('Ошибки чтения данных о студенте:')
        process_errors(errors)
    else:
        if len(warnings) > 0:
            print('Предупреждения при чтении данных о студенте:')
            process_warnings(warnings)
    if student:
        print_student('1', student)
        error = one_gre_transaction(student, redmine, gitlab, email_data)
        if error:
            print('Ошибка при выполнении GRE-транзакции для студента: ')
            process_errors([error])
        else:
            print('Студент успешно добавлен везде')
            errors = add_one_to_groups(student, redmine)
            if len(errors) > 0:
                print('Ошибки добавления студента в группы: ')
                process_errors(errors)
            else:
                print('Студент успешно добавлен в группы')

    quit_server(email_data)
