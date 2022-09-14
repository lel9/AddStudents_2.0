import argparse

from src.lib.helpers import *
from src.lib.logic import one_gre_transaction, add_one_to_groups
from src.lib.minput import parse_header, read_student


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Параметры запуска:')
    parser.add_argument('-i', '--fin', type=str, default='../students.csv',
                        help='Полный путь к входному файлу со студентами (по-умолчанию ../students.csv)')
    parser.add_argument('-m', '--fmail_template', type=str, default='../email1.txt',
                        help='Полный путь к файлу с шаблоном и темой письма (по-умолчанию ../email1.txt)')


    ns = parser.parse_args()
    print(ns)

    # читаем конфиги
    error, config = read_config('../settings.ini')
    if error:
        print('Ошибка чтения настроечного файла settings.ini!')
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

    with open(ns.fin, 'r', encoding="UTF-8") as f:
        errors, warnings, header_data = parse_header(f.readline())
        if len(errors) > 0:
            print('Ошибки чтения заголовка файла ' + ns.fin + ':')
            process_errors(errors)
            quit_server(email_data)
            exit()
        if len(warnings) > 0:
            print('Предупреждения при чтении заголовка файла ' + ns.fin + ':')
            process_warnings(warnings)

        for lnum, line in enumerate(f.readlines()):
            snum = str(lnum + 1)
            errors, warnings, student = read_student(line, header_data)
            if len(errors) > 0:
                print('Ошибки чтения данных о студенте ' + snum + ':')
                process_errors(errors)
            else:
                if len(warnings) > 0:
                    print('Предупреждения при чтении данных о студенте ' + snum + ':')
                    process_warnings(warnings)
                if student:
                    print_student(snum, student)
                    error = one_gre_transaction(student, redmine, gitlab, email_data)
                    if error:
                        print('Ошибка при выполнении GRE-транзакции для студента ' + snum + ': ')
                        process_errors([error])
                    else:
                        print('Студент ' + snum + ' успешно добавлен везде')
                        errors = add_one_to_groups(student, redmine)
                        if len(errors) > 0:
                            print('Ошибки добавления студента ' + snum + ' в группы: ')
                            process_errors(errors)
                        else:
                            print('Студент ' + snum + ' успешно добавлен в группы')

    quit_server(email_data)
