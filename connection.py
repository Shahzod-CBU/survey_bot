from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config
from datetime import datetime
from pandas import DataFrame
import csv, os


script_directory = '/tmp'
database_address = 'mysql+mysqlconnector://xyz'
db_name = 'heroku_abc'


def insert_user(user_id, choices):
    query = f"INSERT INTO {db_name}.survey_results(user_id,choices) VALUES(%s,%s)"
    args = (user_id, choices)

    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)

        cursor = connection.cursor()
        cursor.execute(query, args)
        connection.commit()

    except Error as error:
        print(error, flush=True)

    finally:
        cursor.close()
        connection.close()


def create_result_table():
    use_table = f'USE {db_name};'
    get_num_id = 'SELECT COUNT(DISTINCT id) FROM db_questions;'
    query_drop = 'DROP TABLE IF EXISTS survey_results; '
    query_create = 'CREATE TABLE survey_results(chat_id varchar(50), '

    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(get_num_id)
        num_id = cursor.fetchall()  # returns [(10,)]
        num_id = num_id[0][0]

        for quest_id in range(num_id):
            query_create += f'quest{quest_id + 1} varchar(256), '

        query_create += ('user_name varchar(512), survey_date varchar(10), start_time varchar(15), '
                        'finish_time varchar(15), elapsed_time varchar(15), language varchar(3));')

        cursor.execute(use_table)
        connection.commit()
        cursor.execute(query_drop)
        connection.commit()
        cursor.execute(query_create)
        connection.commit()
    except Error as error:
        print(error, flush=True)
    else:
        print('Successfully created survey_results table', flush=True)
    finally:
        cursor.close()
        connection.close()


def import_questions(file):
    from sqlalchemy import create_engine

    try:
        sqlEngine = create_engine(database_address)
        database_connection = sqlEngine.connect()
        file.to_sql('db_questions', database_connection, if_exists='replace')

    except ValueError as vx:
        print(vx, flush=True)

    except Exception as ex:
        print(ex, flush=True)

    else:
        print('Successfully imported questions.', flush=True)

    finally:
        database_connection.close()

    create_result_table()


def get_process_state():
    query = f"SELECT state FROM {db_name}.process"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()[0][0]
    except Error as error:
        print(error, flush=True)
    else:
        print('Successfully got process state', flush=True)
    finally:
        cursor.close()
        connection.close()

    return records


def get_finished_users():
    query = f"SELECT COUNT(*) FROM {db_name}.survey_results"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()[0][0]
    except Error as error:
        print(error, flush=True)
    finally:
        cursor.close()
        connection.close()

    return records


def get_finished_comments():
    query = f"SELECT COUNT(*) FROM {db_name}.comments"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()[0][0]
    except Error as error:
        print(error, flush=True)
    finally:
        cursor.close()
        connection.close()

    return records


def check_user(user_id):
    query = f"SELECT COUNT(*) FROM {db_name}.survey_results WHERE chat_id = {user_id}"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()[0][0]
    except Error as error:
        print(error, flush=True)
    finally:
        cursor.close()
        connection.close()

    return records

def change_process_state(process_state):
    query = f'UPDATE {db_name}.process SET state = {process_state}'
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
    except Error as error:
        print(error, flush=True)
    else:
        print('Successfully updated process state', flush=True)
    finally:
        cursor.close()
        connection.close()


def get_quests(lang):
    query = f"SELECT id, quests, options, is_multiple, num_columns FROM {db_name}.db_questions WHERE language='{lang}'"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
    except Error as error:
        print(error, flush=True)
    else:
        print('Successfully got questions', flush=True)
    finally:
        cursor.close()
        connection.close()

    return records


def write_results(chat_id, user):
    query = f'INSERT INTO {db_name}.survey_results VALUES ("{chat_id}", '
    for result in user.results:
        query += f'"{result}", '
    query += f'"{user.user_name}", "{user.survey_date}", "{user.start_time}", '
    query += f'"{user.finish_time}", "{user.elapsed_time}", "{user.language}");'
    # print(query)
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
    except Error as error:
        print(error, flush=True)
    else:
        print('Successfully wrote into db.', flush=True)
    finally:
        cursor.close()
        connection.close()


def get_results():
    query = f"SELECT * FROM {db_name}.survey_results;"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
    except Error as error:
        print(error, flush=True)

    finally:
        cursor.close()
        connection.close()

    data_file = os.path.join(script_directory, "output.csv")
    # data_file = "/tmp/output.csv"
    with open(data_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(records)

    print('Successfully got results', flush=True)

    export_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    filename = f'Results {export_time}.csv'
    return filename


def write_comments(chat_id, comment_obj):
    query = f'INSERT INTO {db_name}.comments VALUES ('
    start_time = comment_obj.start_time.strftime("%Y-%m-%d %H-%M")
    query += f'"{chat_id}", "{comment_obj.user_name}", "{start_time}", '
    query += f'"{comment_obj.elapsed_time}", "{comment_obj.comment}");'
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
    except Error as error:
        print(error, flush=True)
    else:
        print('Successfully wrote the comment.', flush=True)
    finally:
        cursor.close()
        connection.close()


def get_comments():
    query = f"SELECT * FROM {db_name}.comments;"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
    except Error as error:
        print(error, flush=True)

    finally:
        cursor.close()
        connection.close()

    data_file = os.path.join(script_directory, "comment.csv")
    with open(data_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(records)

    print('Successfully got comments', flush=True)

    export_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    filename = f'Comments {export_time}.csv'

    return filename


def export_quests():
    query = f"SELECT * FROM {db_name}.db_questions;"
    try:
        db_config = read_db_config()
        connection = MySQLConnection(**db_config)
        cursor = connection.cursor()
        cursor.execute(query)
        records = cursor.fetchall()
    except Error as error:
        print(error, flush=True)

    finally:
        cursor.close()
        connection.close()

    data_file = os.path.join(script_directory, "questions_sql.csv")
    with open(data_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(records)

    export_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    filename = f'Questions_sql {export_time}.csv'

    return filename