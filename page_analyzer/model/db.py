import psycopg2
import os


def connect():
    '''Establishes a database connection

    Returns:
        connection - session instanse
        error - error text message
    '''
    connection, error = None, None
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        connection = psycopg2.connect(DATABASE_URL)
    except psycopg2.OperationalError as e:
        error = (f"Can't establish connection to database. "
                 f"Exception '{e}' type: {type(e)}")

    return (connection, error)
