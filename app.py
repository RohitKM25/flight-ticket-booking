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
    with open(f"{os.path.dirname(__file__)}\\dbinit.sql", "r") as db_file:
        script = db_file.read()
        for i in script.split(';'):
            try:
                if i.strip() != '':
                    mscur.execute(i)
            except mysql.connector.Error as err:
                print_colored(f'ERROR: {err.msg}', type='e')

    files = ['airport', 'airliner']
    for i in files:
        with open(f"{os.path.dirname(__file__)}\\init_data\\{i}.dbinit.csv", "r", newline='', encoding='utf8') as init_file:
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


def get_airliner_from_airliner_code(code):
    mscur.execute('select * from airliner')
    airliners = mscur.fetchall()

    for i in airliners:
        if i['code'] == code:
            return i['name']
    else:
        return 'Unlisted'


def get_airliner_name_from_fare_id(fare_id):
    mscur.execute(
        f'select airliner.name from airliner,flight,fare where fare.id = {fare_id} and flight.id = fare.flight_id and airliner.code = flight.airliner_code', multi=False)
    return mscur.fetchone()['name']


def get_flight_data_from_fare_id(fare_id):
    mscur.execute(
        f'select flight.id "flight_id",flight.departure_on "flight_departure_on",dep.name "departure_airport_name",arr.name "arrival_airport_name",fare.cancellation_fee "fare_cancellation_fee", fare.tag "fare_tag" from airport dep,airport arr,flight,fare where fare.id = {fare_id} and flight.id = fare.flight_id and dep.code = flight.departure_airport_code and arr.code = flight.arrival_airport_code', multi=False)
    return mscur.fetchone()
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
        set_currrent_user(
            {'email': args[0], 'name': args[1], 'password': args[3]})
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


def admin_add_random_flight():
    mscur.execute('select * from airport')
    airports = mscur.fetchall()
    mscur.execute('select * from airliner')
    airliners = mscur.fetchall()

    airplane_id = 'VT-'+join([get_random_letter() for i in range(3)], '')
    airliner_code = random.choice(airliners)['code']
    id = airliner_code + \
        join([str(random.randint(0, 9)) for _ in range(4)], sep='')
    departure_on = get_random_date().strftime(f'%Y-%m-%d %H:%M:00')
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
              'airplane_id': airplane_id,
              'airliner_code': airliner_code}

    print_colored('Added Flight {}', data=[['a', record['id']]])
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
              'max_baggage_weight': max_baggage_weight,
              'meals_included': random.choice([True, False])}

    print_colored('Added Fare {} for {}', data=[
                  ['a', record['tag']], ['a2',  record['flight_id']]])
    new_record('fare', record)
    mysqlcnn.commit()


def find_flights():
    from_location = input_colored('Departure Location: ')
    to_location = input_colored('Arrival Location: ')

    airports = get_table_data('airport')

    departure_airport_code = None
    arrival_airport_code = None

    def check_airport(loc, airport):
        return loc.lower() in airport['city'].lower() or loc.lower() in airport['code'].lower() or loc.lower() in airport['region'].lower() or loc.lower() in airport['name'].lower()

    for i in airports:
        if from_location != '' and check_airport(from_location, i):
            departure_airport_code = i['code']
        if to_location != '' and check_airport(to_location, i):
            arrival_airport_code = i['code']

    now = datetime.datetime.now()
    from_date = input_colored('From: ', default=now.strftime('%Y-%m-%d'))
    to_date = input_colored('To: ', default=now.replace(
        month=now.month+1).strftime('%Y-%m-%d'))
    query_departure_airport_code = f'departure_airport_code = "{departure_airport_code}" and ' if departure_airport_code else ''
    query_arrival_airport_code = f'arrival_airport_code = "{arrival_airport_code}" and ' if arrival_airport_code else ''
    query = f'select * from flight where {query_departure_airport_code}{query_arrival_airport_code}departure_on between "{"2022-01-01" if from_date=="-" else from_date}" and "{"2022-12-31" if to_date=="-" else to_date}"'

    mscur.execute(query)
    flights = mscur.fetchall()
    for i in flights:
        for j in airports:
            if 'departure_airport_code' in i and j['code'] == i['departure_airport_code']:
                del i['departure_airport_code']
                i['departure_airport'] = j['name']
                i['departure_location'] = f"{j['city']}, {j['region']}"
            if 'arrival_airport_code' in i and j['code'] == i['arrival_airport_code']:
                del i['arrival_airport_code']
                i['arrival_airport'] = j['name']
                i['arrival_location'] = f"{j['city']}, {j['region']}"
    for i in flights:
        content = f'''
Flight {{}}, {get_airliner_from_airliner_code(i["airliner_code"])}
From {{}},{i["departure_airport"]} on {{}}
To {{}},{i["arrival_airport"]}
Duration {str(datetime.timedelta(hours=i['duration'])).split(':')[0]}h{str(datetime.timedelta(hours=i['duration'])).split(':')[1]}m.'''
        print_colored(content, data=[['a', i["id"]], ['a', i["departure_location"]], [
                      'a2', i["departure_on"].strftime('%Y-%m-%d %H:%M:%S')], ['a', i["arrival_location"]]])


def get_fares():
    flight_id = input_colored('Flight Id: ')
    if not flight_id:
        return

    mscur.execute(
        f'select * from fare where flight_id = "{flight_id}" and total_seats > (select count(*) from booking where booking.is_cancelled = false and booking.fare_id = fare.id)')
    fares = mscur.fetchall()

    if len(fares) == 0:
        print_colored(
            'Fares for {} are unavailable. Or the flight id entered may be incorrect.')

    min_amount = min([i['amount'] for i in fares])
    max_amount = max([i['amount'] for i in fares])

    print_colored('Fares for flight {}:', data=[['a', flight_id]])
    for i in fares:
        if i['amount'] == min_amount:
            print('\n'+tabulate([[f'''
{FORE_COLORS['a']}{i["tag"].title()}{FORE_COLORS['r']}
{i['description'].capitalize()}.
Cabin Bag Weight: {i['max_cabin_bag_weight']}
Baggage Weight: {i['max_baggage_weight']}
Meals Included: {'Yes' if i['meals_included'] else 'No'}
Rs {FORE_COLORS['s'] if i["amount"] == min_amount else FORE_COLORS['e'] if i["amount"] == max_amount else FORE_COLORS['w']}{i["amount"]}{FORE_COLORS['r']}''']], tablefmt='grid', headers=('BEST PRICE',)))
        else:
            content = f'''
{{}}
{i['description'].capitalize()}.
Cabin Bag Weight: {i['max_cabin_bag_weight']}
Baggage Weight: {i['max_baggage_weight']}
Meals Included: {'Yes' if i['meals_included'] else 'No'}
Rs {{}}'''
            print_colored(content, data=[['a', i["tag"].title()], [
                's' if i["amount"] == min_amount else 'e' if i["amount"] == max_amount else 'w', str(i["amount"])]])


def admin_add_random_flight_repeat():
    for _ in range(int(input_colored('Number of records: '))):
        admin_add_random_flight()
    print(f"Finished")


def admin_add_random_fare_repeat():
    for _ in range(int(input_colored('Number of records: '))):
        admin_add_random_fare()
    print(f"Finished")


def book():
    flight_id = input_colored('Enter flight id: ')
    fare_tag = input_colored('Enter fare tag: ')
    if SESSION_STORAGE['current_user'] == '':
        print_colored('No user signed in.', type='e')
        return

    try:
        mscur.execute(
            f'select * from fare where fare.tag = "{fare_tag}" and fare.flight_id = "{flight_id}"', multi=False)
        fare = mscur.fetchone()
        if input_colored('Confirm Booking: ', default='y').lower() != 'y':
            print('Booking cancelled.', type='e')
            return
        record = {'user_email': SESSION_STORAGE['current_user'],
                  'fare_id': fare['id'], }
        new_record('booking', record)
        print_colored('Successfullly booked flight.', type='s')
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')


def my_bookings():
    if SESSION_STORAGE['current_user'] == '':
        print_colored('No user signed in.', type='e')
        return

    user = get_user_by_email(SESSION_STORAGE['current_user'])

    print_colored('{}\'s bookings', data=[
                  ['a', user['name']]])

    mscur.execute(
        f'select * from booking where user_email = "{user["email"]}" and is_cancelled = false order by booked_on desc')
    bookings = mscur.fetchall()

    for i in range(len(bookings)):
        airliner_name = get_airliner_name_from_fare_id(bookings[i]["fare_id"])
        flight_data = get_flight_data_from_fare_id(bookings[i]['fare_id'])
        content = '''
({}) {}
Booking for {} Flight {}
From {} to {}
On {}.
Cancellation Fee: {}'''
        print_colored(content, data=[['a2', str(i)], ['a',  flight_data['fare_tag'].title()], ['a', airliner_name], ['a', flight_data['flight_id']], ['a', flight_data['departure_airport_name']], [
                      'a', flight_data['arrival_airport_name']], ['a', flight_data['flight_departure_on'].strftime('%Y-%m-%d %H:%M:%S')], ['e', str(flight_data['fare_cancellation_fee'])]])
    return bookings


def cancel_booking():
    bookings = my_bookings()
    print()
    booking_index = int(input_colored('Enter Booking Index: '))

    flight_data = get_flight_data_from_fare_id(
        bookings[booking_index]['fare_id'])

    if input_colored('Are you sure you want to cancel booking for {},\nwith cancellation fee {}? ', default='y', data=[['a', flight_data['flight_id']], ['e', str(flight_data['fare_cancellation_fee'])]]).lower() != 'y':
        print('Booking cancelled.')
        return

    try:
        mscur.execute(
            f'update booking set is_cancelled = true where id = {bookings[booking_index]["id"]}')
        mysqlcnn.commit()
        print_colored('Cancelled booking.', type='s')
    except mysql.connector.Error as err:
        print_colored(f'ERROR: {err.msg}', type='e')


# dictionary of all commands
commands = {
    'signin': {'cmd': sign_in, 'desc': 'Signs a user, using email and password. User stored locally.'},
    'signup': {'cmd': sign_up, 'desc': 'Adds the user to database.'},
    'signout': {'cmd': sign_out, 'desc': 'Removes the signed in user from local storage.'},
    'find flights': {'cmd': find_flights, 'desc': 'Finds available flights, from given departure and arrival airports, between provided dates.'},
    'get fares': {'cmd': get_fares, 'desc': 'Gets the fares for the provided flight id. Shows the best and the worst deal.'},
    'book': {'cmd': book, 'desc': 'Books the flight with given no. and fare tag.'},
    'my bookings': {'cmd': my_bookings, 'desc': 'View your ticket bookings.'},
    'cancel booking': {'cmd': cancel_booking, 'desc': 'Delete a booking of provided booking id.'},
    'admin add': {'cmd': admin_add, 'desc': 'Add a new record into the given table.'},
    'admin add random flights': {'cmd': admin_add_random_flight_repeat, 'desc': 'Adds a new flights with random data.'},
    'admin add random fares': {'cmd': admin_add_random_fare_repeat, 'desc': 'Adds a new fares with random data.'},
    'admin view': {'cmd': admin_view, 'desc': 'Displays records of given table.'},


}

# main
# setting up local storage
if not os.path.exists(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json'):
    #     print_colored('Settings file exists.', type='s')
    # else:
    print_colored('Settings file does not exist.', type='e')
    print_colored('Creating settings file with default settings.')
    with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'w') as settings_file:
        json.dump(DEFAULT_SETTINGS, settings_file)
        print_colored('Settings file created.', type='s')
with open(f'{os.path.expanduser("~")}\\flight-ticket-booking-settings.json', 'r') as settings_file:
    LOCAL_STORAGE = json.load(settings_file)
# print_colored('Loaded Settings.', type='s')

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
        # print_colored('Connected to Mysql.', type='s')
        app_settings_set('mysqlconnection:host', args[0])
        app_settings_set('mysqlconnection:port', args[1])
        app_settings_set('mysqlconnection:user', args[2])
        app_settings_set('mysqlconnection:password', args[3])
except mysql.connector.Error as err:
    print_colored(f'ERROR: {err.msg}', type='e')

mscur = mysqlcnn.cursor(dictionary=True)

# checking database
if not check_database_exists():
    #     print_colored('Database "{}" exists.', type='s',
    #                   data=[['a', 'flight_ticket_booking']])
    # else:
    print_colored(
        'Database does not exist.', type='e')
    print_colored(
        'Initializing database.', type='i')
    initialize_database()


print_colored('FLIGHT TICKET BOOKING', type='a')
print_colored('---------------------')
print_colored('By {}, {}, {}.', data=[['a2', 'ROHIT K MANOJ'], [
              'a2', 'DARSHAN M'], ['a2', 'AADI DEV S']])
print()

# checking user signed in.
if LOCAL_STORAGE['app:signed_in_user'] != '':
    user = get_user_by_email(LOCAL_STORAGE['app:signed_in_user'])
    if user:
        SESSION_STORAGE['current_user'] = user['email']
        print_colored('Hi {}!', data=[['a', user['name']]])
    else:
        print_colored('{} signed in but not recognised. Please sign in again to rectify issue.', data=[
                      ['a', SESSION_STORAGE['current_user']]], type='w')
else:
    print_colored('No user signed in. use "{}"',
                  data=[['a', 'signin']], type='w')
print_colored('Commands:')
for i in commands:
    print_colored('\t{} => {}', data=[['a2', i], ['d', commands[i]['desc']]])

# command loop
while True:
    cmd = input_colored('>>> ').lower()
    if cmd in ('exit', 'quit', 'q', 'e'):
        break
    elif cmd in commands.keys():
        commands[cmd]['cmd']()
        print()
        print('-'*10+'END'+'-'*10)
    else:
        print_colored(f'Command not found.', type='e')

cm.deinit()
