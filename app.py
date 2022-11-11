import json
import mysql.connector
import mysql.connector as mysqlcnr
import os
import csv
import random
import datetime
from utils import *

cm.init(convert=True)
# prerequisites

DEFAULT_SETTINGS = {
    'general:show_startup_status': True,
    'mysqlconnection:host': '',
    'mysqlconnection:port': 0,
    'mysqlconnection:user': '',
    'mysqlconnection:password': '',
    'app:signed_in_user': '',
    'app:signed_in_user_password': ''}

LOCAL_STORAGE = None

# data required for a session.
SESSION_STORAGE = {
    'current_user': ''
}


def check_database_exists():
    try:
        mscur.execute('show databases')
        dbs = mscur.fetchall()
        if 'flight_ticket_booking' in [i['Database'] for i in dbs]:
            mscur.execute('use flight_ticket_booking')
            return True
        else:
            return False
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')


def get_user_by_email(email):
    try:
        mscur.execute(
            f'select * from user where email = "{email}"', multi=False)
        return mscur.fetchone()
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')


def set_currrent_user(user):
    if user:
        SESSION_STORAGE['current_user'] = user['email']
        app_settings_set('app:signed_in_user', user['email'])
        app_settings_set('app:signed_in_user_password', user['password'])
        print_colored('Signed user in.', type='s')


def new_record(table, data):
    try:
        keys = join(list(data.keys()), ',')
        values = str(tuple(data.values()))
        values = values if ',)' not in values else values[:-2] + ')'
        mscur.execute('insert into {}({}) values {}'.format(
            table, keys, values))
        mysqlcnn.commit()
        return True
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')
        return False


def new_user(values):
    cols = ['email', 'name', 'phone', 'password']
    try:
        new_record('user', {cols[i]: values[i] for i in range(len(cols))})
        mysqlcnn.commit()
        return True
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')
        return False


def initialize_database():
    with open(f"dbinit.sql", "r") as db_file:
        script = db_file.read()
        for i in script.split(';'):
            try:
                if i.strip() != '':
                    mscur.execute(i)
            except mysql.connector.Error as err:
                print_colored(f'ERROR: {err.msg}', type='e')

    files = ['manufacturer', 'airplane_model', 'airport', 'airliner']
    for i in files:
        with open(f"init_data\\{i}.dbinit.csv", "r", newline='') as init_file:
            content = list(csv.reader(init_file))
            content = [{content[0][j]:content[i][j] for j in range(
                len(content[0]))} for i in range(1, len(content))]
            try:
                mscur.execute(f'desc {i}')
                cols = mscur.fetchall()
                fields = [i['Field'] for i in cols]
                for k in range(len(content)):
                    if 'id' in fields:
                        content[k]['id'] = k+1
                    new_record(i, content[k])
            except mysql.connector.Error as err:
                print_colored(f'ERROR: {err.msg}', type='e')
            print_colored('Loaded data into "{}".', type='s', data=[['a', i]])
    print_colored('Successfully loaded into database.', type='s')


def app_settings_set(key, value):
    settings = None
    with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'r') as settings_file:
        settings = json.load(settings_file)
    if not settings:
        print_colored('Settings file not corrupted.', type='e')
    with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'w') as settings_file:
        settings[key] = value
        json.dump(settings, settings_file)
        LOCAL_STORAGE[key] = value


def get_table_data(table_name, columns=None, conditions=None):
    try:
        mscur.execute(
            f'select {join(columns,",") if columns else "*"} from {table_name}{" where "+join(conditions) if conditions else ""}')
        return mscur.fetchall()
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')

# app commands


def sign_in():
    '''
    Signs in the user using email and password from the db.
    '''
    args = [input_colored('Email: '), input_colored('Password: ')]
    user = get_user_by_email(args[0])
    if user:
        if args[1] == user['password']:
            set_currrent_user(user)
        else:
            print_colored('Incorrect password.', type='e')
    else:
        print_colored('Incorrect email.', type='e')


def sign_up():
    '''
    Signs the user up, adds user to database.
    '''
    args = [input_colored('Email: '), input_colored('Name: '), input_colored(
        'Phone Number: '), input_colored('Password: ')]

    if new_user(args):
        print_colored('Added new user {}', data=[['a', args[1]]], type='s')
        set_currrent_user({'email': args[0], 'name': args[1]})
    else:
        print_colored('Incorrect email.', type='e')


def sign_out():
    '''
    Signs the user out.
    '''
    del SESSION_STORAGE['current_user']
    app_settings_set('app:signed_in_user', '')
    app_settings_set('app:signed_in_user_password', '')
    print_colored('Signed user out.', type='s')


def view_settings():
    with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'r') as settings_file:
        settings = json.load(settings_file)
        tabed([{'Category': i.split(':')[0], 'Setting':i.split(":")
              [1], 'Current Value':settings[i]} for i in settings])


def admin_add():
    type = input_colored('Table: ')
    args = {}
    try:
        mscur.execute('show tables')
        tables = mscur.fetchall()
        if type in get_list_from_1col_dict(tables):
            mscur.execute(f'desc {type}')
            table_columns = mscur.fetchall()
            tabed(table_columns)
            for i in table_columns:
                if i['Default']:
                    continue
                args[i["Field"]] = input_colored_type_casted(
                    f'{i["Field"]}: ', i['Type'])
        else:
            print_colored(f'Table does not exist.', type='e')
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')
        return False
    new_record(type, args)


def admin_view():
    type = input_colored('Table: ')
    try:
        mscur.execute('show tables')
        tables = mscur.fetchall()
        if type in get_list_from_1col_dict(tables):
            mscur.execute(f'select * from {type}')
            table_rows = mscur.fetchall()
            if len(table_rows) == 0:
                print('Empty Table')
                return True
            tabed(table_rows)
            return True
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')
        return False


def admin_add_random_airplane():
    mscur.execute('select * from airplane_model')
    airplane_models = mscur.fetchall()
    mscur.execute('select * from airliner')
    airliners = mscur.fetchall()

    id = 'VT-'+join([get_random_letter() for i in range(3)], '')
    seats = random.randint(10, 50)*10
    airplane_model_id = random.choice(airplane_models)['id']
    airliner_code = random.choice(airliners)['code']

    record = {'id': id, 'seats': seats,
              'airplane_model_id': airplane_model_id, 'airliner_code': airliner_code}

    tabed([record])
    if input_colored('Add to database? ', default='y').lower() != 'y':
        return
    new_record('airplane', record)
    mysqlcnn.commit()


def admin_add_random_flight():
    mscur.execute('select * from airplane')
    airplanes = mscur.fetchall()
    mscur.execute('select * from airport')
    airports = mscur.fetchall()

    airplane = random.choice(airplanes)
    id = airplane['airliner_code'] + \
        join([str(random.randint(0, 9)) for _ in range(4)], sep='')
    departure_on = datetime.datetime(2000 + random.randint(0, 99), random.randint(1, 12), random.randint(
        1, 31), random.randint(0, 23), random.randint(0, 5)*10).strftime(f'%Y-%m-%d %H:%M:00')
    departure_airport_code = random.choice(airports)['code']
    stops = ''
    duration = random.randint(1, 5)
    arrival_airport_code = random.choice(
        [i for i in airports if i['code'] != departure_airport_code])['code']

    record = {'id': id,
              'departure_on': departure_on,
              'departure_airport_code': departure_airport_code,
              'stops': stops,
              'duration': duration,
              'arrival_airport_code': arrival_airport_code,
              'airplane_id': airplane['id']}

    tabed([record])
    if input_colored('Add to database? ', default='y').lower() != 'y':
        return
    new_record('flight', record)
    mysqlcnn.commit()


def admin_add_random_fare():
    mscur.execute('select * from flight')
    flights = mscur.fetchall()

    flight_id = random.choice(flights)['id']
    total_seats = random.randint(5, 10)*10
    tag = join([get_random_letter() for i in range(random.randint(5, 10))], '')
    description = join([get_random_letter()
                       for i in range(random.randint(10, 30))], '')
    amount = random.randint(5, 25)*1000
    cancellation_fee = random.randint(1, 9)*100
    max_cabin_bag_weight = random.randint(1, 10)
    max_baggage_weight = random.randint(1, 10)*10

    record = {'flight_id': flight_id,
              'total_seats': total_seats,
              'tag': tag,
              'description': description,
              'amount': amount,
              'cancellation_fee': cancellation_fee,
              'max_cabin_bag_weight': max_cabin_bag_weight,
              'max_baggage_weight': max_baggage_weight}

    tabed([record])
    if input_colored('Add to database? ', default='y').lower() != 'y':
        return
    new_record('fare', record)
    mysqlcnn.commit()


def find_flights():
    from_location = input_colored('Departure Location: ')
    to_location = input_colored('Arrival Location: ')

    airports = get_table_data('airport')

    departure_airport_code = None
    arrival_airport_code = None

    for i in airports:
        if i['location'].lower() == from_location.lower():
            departure_airport_code = i['code']
        if i['location'].lower() == to_location.lower():
            arrival_airport_code = i['code']

    now = datetime.datetime.now()
    from_date = input_colored('From: ', default=now.strftime('%Y-%m-%d'))
    now.replace(day=now.day+1)
    to_date = input_colored('To: ', default=now.strftime('%Y-%m-%d'))
    mscur.execute(
        f'select * from flight where {"departure_airport_code = "+departure_airport_code+" and " if departure_airport_code else ""}{"arrival_airport_code = "+arrival_airport_code+" and " if arrival_airport_code else ""}departure_on between "{"2000-01-01" if from_date=="-" else from_date}" and "{"2099-12-31" if to_date=="-" else to_date}"')
    flights = mscur.fetchall()
    for i in flights:
        for j in airports:
            if 'departure_airport_code' in i and j['code'] == i['departure_airport_code']:
                del i['departure_airport_code']
                i['departure_airport'] = j['name']
                i['departure_location'] = j['location']
            if 'arrival_airport_code' in i and j['code'] == i['arrival_airport_code']:
                del i['arrival_airport_code']
                i['arrival_airport'] = j['name']
                i['arrival_location'] = j['location']
    tabed(flights)


def settings():
    print_colored('Settings Menu:')
    print_colored('')


# dictionary of all commands
commands = {
    'signin': sign_in,
    'signup': sign_up,
    'signout': sign_out,
    'find flights': find_flights,
    'admin add': admin_add,
    'admin add random airplane': admin_add_random_airplane,
    'admin add random flight': admin_add_random_flight,
    'admin add random fare': admin_add_random_fare,
    'admin view': admin_view,
    'settings view': view_settings,
}

# main
print_colored('FLIGHT TICKET BOOKING', type='a')
print_colored('By {}, {}, {}.', data=[['a', 'ROHIT K MANOJ'], [
              'a', 'DARSHAN M'], ['e', 'AADI DEV S']])
print()

# setting up local storage
if os.path.exists(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json'):
    print_colored('Settings file exists.', type='s')
else:
    print_colored('Settings file does not exist.', type='e')
    print_colored('Creating settings file with default settings.')
    with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'w') as settings_file:
        json.dump(DEFAULT_SETTINGS, settings_file)
        print_colored('Settings file created.', type='s')
with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'r') as settings_file:
    LOCAL_STORAGE = json.load(settings_file)
print_colored('Loaded Settings.', type='s')

# mysql connection setup
if LOCAL_STORAGE['mysqlconnection:password']:
    args = [LOCAL_STORAGE['mysqlconnection:host'], LOCAL_STORAGE['mysqlconnection:port'],
            LOCAL_STORAGE['mysqlconnection:user'], LOCAL_STORAGE['mysqlconnection:password']]
else:
    args = [input_colored('host: ', default='localhost'),
            input_colored(
                'port: ', default='3306'),
            input_colored('user: ', default='root'),
            input_colored('password: ')]

mysqlcnn = None
try:
    mysqlcnn = mysqlcnr.connect(
        host=args[0],
        port=args[1],
        user=args[2],
        password=args[3])
    if mysqlcnn.is_connected():
        print_colored('Connected to Mysql.', type='s')
        app_settings_set('mysqlconnection:host', args[0])
        app_settings_set('mysqlconnection:port', args[1])
        app_settings_set('mysqlconnection:user', args[2])
        app_settings_set('mysqlconnection:password', args[3])
except mysql.connector.Error as err:
    print_colored(f'ERROR: {err.msg}', type='e')

mscur = mysqlcnn.cursor(dictionary=True)

# checking database
if check_database_exists():
    print_colored('Database "{}" exists.', type='s',
                  data=[['a', 'flight_ticket_booking']])
else:
    print_colored(
        'Database does not exist.', type='e')
    print_colored(
        'Initializing database.', type='i')
    initialize_database()

# checking user signed in.
if LOCAL_STORAGE['app:signed_in_user'] != '':
    user = get_user_by_email(LOCAL_STORAGE['app:signed_in_user'])
    if user:
        print_colored('Hi {}!', data=[['a', user['name']]])
    else:
        print_colored('{} signed in but not recognised. Please sign in again to rectify issue.', data=[
                      ['a', SESSION_STORAGE['current_user']]], type='w')
else:
    print_colored('No user signed in. use "{}"',
                  data=[['a', 'signin']], type='w')
print()

# command loop
while True:
    cmd = input_colored('>> ').lower()
    if cmd in ('exit', 'quit', 'q', 'e'):
        break
    elif cmd in commands.keys():
        commands[cmd]()
    else:
        print_colored(f'Command not found.', type='e')

cm.deinit()
