from page_analyzer.app import app
from psycopg2.extras import NamedTupleCursor
from datetime import datetime
from flask import url_for
import os


with app.test_request_context():
    CORRECT_URL = "http://gmail.com"
    INCORRECT_URL = "http://wrong.com"
    GET_PAGE = url_for('show_url', id=1)
    POST_PAGE = url_for('check', url_id=1)


def add_url_to_db(connection, url_name):
    with connection as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            created_at = datetime.utcnow()
            curs.execute("""INSERT INTO urls(name, created_at)
                            VALUES (%s, %s)""",
                         (url_name, created_at))


def test_basic_content(get_test_db):
    connection = get_test_db
    add_url_to_db(connection, CORRECT_URL)
    client = app.test_client()
    response = client.get(GET_PAGE)

    assert response.status_code == 200
    assert CORRECT_URL in response.text
    assert "Запустить проверку" in response.text


def test_missing_db_connection():
    actual_database_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = "wrong"

    try:
        client = app.test_client()
        response = client.get(GET_PAGE)
    finally:
        os.environ["DATABASE_URL"] = actual_database_url

    assert response.status_code == 500
    assert response.request.path == GET_PAGE
    assert "Невозможно установить соединение с базой данных." in response.text


def test_check_correct_url(get_test_db):
    H1 = "Sign in"
    TITLE = "Gmail"
    DESCRIPTION = (
        "Gmail is email that’s intuitive, efficient, and useful."
        " 15 GB of storage, less spam, and mobile access.")

    connection = get_test_db
    add_url_to_db(connection, CORRECT_URL)
    client = app.test_client()

    # 1st check
    pre_1st_time = datetime.utcnow()
    response1 = client.post(POST_PAGE, follow_redirects=True)
    assert response1.status_code == 200
    assert response1.request.path == GET_PAGE
    assert "Страница успешно проверена" in response1.text
    assert H1 in response1.text
    assert TITLE in response1.text
    assert DESCRIPTION in response1.text

    # 2nd check
    pre_2nd_time = datetime.utcnow()
    response2 = client.post(POST_PAGE, follow_redirects=True)
    assert response2.status_code == 200
    assert response2.request.path == GET_PAGE
    assert "Страница успешно проверена" in response2.text

    # database asserts
    with connection as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("SELECT * FROM checks")
            db_records = curs.fetchall()
    assert len(db_records) == 2
    assert db_records[0].url_id == db_records[1].url_id == 1
    assert db_records[0].status_code == db_records[1].status_code == 200
    assert db_records[0].h1 == db_records[1].h1 == H1
    assert db_records[0].title == db_records[1].title == TITLE
    assert db_records[0].description == DESCRIPTION
    assert db_records[1].description == DESCRIPTION
    assert pre_1st_time <= db_records[0].created_at <= pre_2nd_time
    assert pre_2nd_time <= db_records[1].created_at


def test_check_incorrect_url(get_test_db):

    connection = get_test_db
    add_url_to_db(connection, INCORRECT_URL)
    client = app.test_client()

    response = client.post(POST_PAGE, follow_redirects=True)
    assert response.status_code == 422
    assert response.request.path == GET_PAGE
    assert "Произошла ошибка при проверке" in response.text

    with connection as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute("SELECT * FROM checks")
            db_records = curs.fetchall()
    assert len(db_records) == 0
