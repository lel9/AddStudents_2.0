import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.lib.constants import LOGIN_PREFIX, EMAIL_TIMEOUT
from src.lib.helpers import random_pass, add_zero, exc_to_str


def delete_one_from_redmine(student, redmine):
    redmine.user.delete(student['redmine_id'])


def delete_one_from_gitlab(student, gitlab):
    gitlab.users.delete(student['gitlab_id'])


def add_one_to_redmine(student, redmine):
    user = redmine.user.create(
        login=student['stud_id'],
        password=student['passw'],
        firstname=student['fname'],
        lastname=student['lname'],
        mail=student['email'],
        mail_notification='all',
        must_change_passwd=True)
    student['redmine_id'] = str(user.id)


def add_one_to_gitlab(student, gitlab):
    user = gitlab.users.create({'email': student['email'],
                                'password': student['passw'],
                                'username': student['stud_id'],
                                'name': student['lname'] + ' ' + student['fname'],
                                'external': True,
                                'skip_confirmation': True})
    student['gitlab_id'] = str(user.id)


def create_mail(student, email_template):
    return email_template.replace("%rm_login%", student['stud_id']) \
        .replace("%rm_pass%", student['passw']) \
        .replace("%gl_login%", student['stud_id']) \
        .replace("%gl_pass%", student['passw']) \
        .replace("%name%",
                 student['lname'] + ' ' + student['fname']
                 if student['fname'] != '-' else
                 student['lname'])


def send_one_mail(student, email_data):
    msg = MIMEMultipart()
    msg['From'] = email_data['from']
    msg['To'] = student['email']
    msg['Subject'] = email_data['subject']
    text = create_mail(student, email_data['template'])
    #print('Щас как отправим письмо для ' + student['email'] + ' от ' +
    #      email_data['from'] + ' с темой ' + email_data['subject'])
    #print(text)
    msg.attach(MIMEText(text, 'plain'))
    msg = msg.as_string()
    email_data['smtp_server'].sendmail(email_data['from'], [student['email']], msg)
    time.sleep(EMAIL_TIMEOUT)


def get_last_used_id(redmine):
    offset = 0
    last_used_id = 0
    step = 100
    while True:
        users = redmine.user.all(offset=offset, limit=step)
        if len(users) == 0:
            break
        for user in users:
            if user.login.startswith(LOGIN_PREFIX):
                id = int(user.login.split(LOGIN_PREFIX[-1])[1])
                if id > last_used_id:
                    last_used_id = id
        offset += step
    return last_used_id


stud_id = -1


def get_next_stud_id(redmine):
    global stud_id
    if stud_id == -1:
        stud_id = get_last_used_id(redmine)

    stud_id = stud_id + 1
    return LOGIN_PREFIX + add_zero(str(stud_id))


def one_gre_transaction(student, redmine, gitlab, email_data):
    rm_success, gl_success = 0, 0
    try:
        student['stud_id'] = get_next_stud_id(redmine)
        student['passw'] = random_pass(8)
        add_one_to_redmine(student, redmine)
        rm_success = 1
        add_one_to_gitlab(student, gitlab)
        gl_success = 1
        send_one_mail(student, email_data)
    except Exception as e:
        if rm_success:
            try:
                delete_one_from_redmine(student, redmine)
            except Exception as e:
                print('Не удалось откатить транзакцию! Ошибка удаления из Redmine студента ' + student)
                print(exc_to_str(e))
        if gl_success:
            try:
                delete_one_from_gitlab(student, gitlab)
            except Exception as e:
                print('Не удалось откатить транзакцию! Ошибка удаления из Redmine студента ' + student)
                print(exc_to_str(e))
        return exc_to_str(e)
    return None


group_id_map = dict()


def get_group_id(group_name, redmine):
    global group_id_map
    if group_name in group_id_map:
        return group_id_map[group_name]

    # тк редмайн не поддерживает поиск по имени группы, тупо перебираем всё
    all_groups = redmine.group.all()
    for group in all_groups:
        if group.name == group_name:
            group_id_map[group_name] = group.id
            return group.id

    raise Exception('Группа ' + group_name + ' не найдена в Redmine')


def add_one_to_groups(student, redmine):
    errors = []
    for group in student['groups']:
        try:
            group_id = get_group_id(group, redmine)
            user_ids = set()
            group = redmine.group.get(group_id, include=['users'])
            # забираем старых юзеров, чтобы не потерялись
            for user in group.users:
                user_ids.add(user.id)
            # берем нового юзера
            user_ids.add(student['redmine_id'])
            # обновляем
            redmine.group.update(group_id, user_ids=list(user_ids))
        except Exception as e:
            errors.append(exc_to_str(e))

    return errors


def get_redmine_user_id(login, redmine):
    users = redmine.user.filter(name=login)
    # filter очень хитер
    # например для name=stud_0 он вернет пользователей с логинами stud_00, stud_01, stud_02 и т д
    # поэтому мы ходим по юзерам и точно выбираем нужного
    for user in users:
        if user.login == login:
            return user.id
    raise Exception("Студент с логином " + login + " не найден в Redmine")


def get_gitlab_user_id(login, gitlab):
    users = gitlab.users.list(username=login)
    if len(users) > 0:
        return users[0].id
    raise Exception("Студент с логином " + login + " не найден в Gitlab")


def add_one_to_groups_by_login(login, group, redmine):
    try:
        redmine_id = get_redmine_user_id(login, redmine)
    except Exception as e:
        return exc_to_str(e)

    student = dict()
    student['redmine_id'] = redmine_id
    student['groups'] = [group]
    errors = add_one_to_groups(student, redmine)
    if len(errors) > 0:
        return errors[0]

    return None


def delete_user(login, redmine, gitlab):
    errors = []
    try:
        redmine_id = get_redmine_user_id(login, redmine)
        student = dict()
        student['redmine_id'] = redmine_id
        delete_one_from_redmine(student, redmine)
    except Exception as e:
        errors.append(exc_to_str(e))

    try:
        gitlab_id = get_gitlab_user_id(login, gitlab)
        student = dict()
        student['gitlab_id'] = gitlab_id
        delete_one_from_gitlab(student, gitlab)
    except Exception as e:
        errors.append(exc_to_str(e))

    return errors
