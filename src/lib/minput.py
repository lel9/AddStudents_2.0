def parse_header(header):
    errors = []
    warnings = []
    header_data = dict({'name_id': -1,
                        'email_id': -1,
                        'eu_id_id': -1,
                        'groups_id': -1,
                        'field_count': 0})

    headers = header.strip().split('\t')
    if 'ФИО' in headers:
        header_data['name_id'] = headers.index('ФИО')
    if 'почта' in headers:
        header_data['email_id'] = headers.index('почта')
    if header_data['name_id'] == -1 or header_data['email_id'] == -1:
        errors.append('Должны быть указаны ФИО и почта через символ табуляции')
        return errors, warnings, header_data

    header_data['field_count'] += 2
    if 'eu_id' in headers:
        header_data['eu_id_id'] = headers.index('eu_id')
        header_data['field_count'] += 1
    # else:
    # warnings.append(format_warning(1, 'Не указан eu_id'))

    if '[группы]' in headers:
        header_data['groups_id'] = headers.index('[группы]')
        header_data['field_count'] += 1
    else:
        warnings.append('Не указаны [группы]')

    return errors, warnings, header_data


def get_fname_and_lname(sname):
    name = sname.split(' ')
    if len(name) == 1:
        fname, lname = '-', name[0]
    else:
        fname, lname = ' '.join([x for x in name[1:] if len(x) > 0]), name[0]
    return fname, lname


# вход: "[ ИУ7-53Б, АА ]"
# выход: массив строк ["ИУ7-53Б", "AA"]
def get_groups(sgroups):
    errors = []
    warnings = []
    if len(sgroups) < 2:
        warnings.append('Длина строки [группы] меньше 2')
        return errors, warnings, []
    if sgroups[0] != '[' or sgroups[-1] != ']':
        warnings.append('Что-то не так с массивом групп: нет \'[\' и/или \']\'')
        return errors, warnings, []
    return errors, warnings, [x for x in sgroups[1:-1].replace(' ', '').split(',') if len(x) > 0]


def read_student(line, header_data):
    errors = []
    warnings = []

    line = line.strip()
    if len(line) == 0:
        return [], [], None

    raw_data = line.strip().split('\t')
    data = [x.strip() for x in raw_data if len(x.strip()) > 0]
    if len(data) != header_data['field_count']:
        errors.append('Количество полей не равно ' + str(header_data['field_count']))
        return errors, [], None

    fname, lname = get_fname_and_lname(data[header_data['name_id']])
    email = data[header_data['email_id']]
    eu_id = data[header_data['eu_id_id']] if header_data['eu_id_id'] != -1 else -1
    if header_data['groups_id'] == -1:
        groups = []
    else:
        errors_g, warnings_g, groups = get_groups(data[header_data['groups_id']])
        for e in errors_g: errors.append(e)
        for w in warnings_g: warnings.append(w)

    return errors, warnings, {
        'fname': fname, 'lname': lname,
        'email': email, 'eu_id': str(eu_id),
        'groups': groups
    }


def read_student_cmd(ns):
    fname, lname = get_fname_and_lname(ns.name)
    errors, warnings, groups = get_groups(ns.groups)
    return errors, warnings, {
        'fname': fname, 'lname': lname,
        'email': ns.email, 'eu_id': str(ns.eu_id),
        'groups': groups
    }
