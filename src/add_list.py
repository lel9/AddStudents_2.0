import argparse

from src.helpers import try_open, read_config, get_redmine, get_gitlab
from src.logic import one_gre_transaction, add_one_to_groups
from src.minput import parse_header, read_student


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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Параметры запуска:')
    parser.add_argument('-i', '--fin', type=str, default='../students.csv',
                        help='Полный путь к входному файлу со студентами (по-умолчанию ./students.csv)')

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

    smtp_client = ''

    with open(ns.fin, 'r', encoding="UTF-8") as f:
        errors, warnings, header_data = parse_header(f.readline())
        if len(errors) > 0:
            print('Ошибки чтения заголовка файла ' + ns.fin + ':')
            process_errors(errors)
            exit()
        if len(warnings) > 0:
            print('Предупреждения при чтении заголовка файла ' + ns.fin + ':')
            process_warnings(warnings)

        for lnum, line in enumerate(f.readlines()):
            snum = str(lnum + 2)
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
                    error = one_gre_transaction(student, redmine, gitlab, smtp_client)
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
