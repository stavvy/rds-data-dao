from rds_data_dao.db_util import (create_update_clause, format_sql,
                                  format_string_list, get_cast, make_list,
                                  quote_escape, try_parse_date, unique_on_key)

BAD_INPUT_STRING = "123123123.:-' and $%$&{|}{|[\\+_+//%;';';<?>$&(#$*($"
FILTERED_BAD_INPUT_STRING = '123123123.:- and '


def test_create_update_clause():
    obj = {
        "items": 5,
        "status": "closed"
    }

    clause = create_update_clause(obj)
    assert clause == "items='5', status='closed'"

def test_create_update_clause_with_nulls():
    obj = {
        "items": "",
        "status": None
    }

    clause = create_update_clause(obj)
    assert clause == "items='', status=null"

def test_create_update_clause_escapes():
    obj = {
        "\>items;": ">/;",
        "status/|": ";;;"
    }

    clause = create_update_clause(obj)
    assert clause == "%5C%3Eitems%3B='%3E%2F%3B', status%2F|='%3B%3B%3B'"


def test_make_list_ints():
    items = [1, 2, 3]
    s = make_list(items)
    assert s == "('1','2','3')"


def test_make_list_str():
    items = ['', "'quoted'", 'regular']
    s = make_list(items)
    assert s == "('','%27quoted%27','regular')"


def test_quote_escape_does_not_escape_user_id():
    user_id = 'auth0|5db190ade7d02d0c5c757163'
    s = quote_escape(user_id)
    assert s == user_id


def test_quote_escape_does_not_escape_email():
    email = 'test@test.com'
    s = quote_escape(email)
    assert s == email


def test_quote_escape_does_not_escape_safe_chars():
    s = 'new|file|name'
    res = quote_escape(s)
    assert s == res


def test_format_sql():
    s = "%s %s::order_types %s::json"
    res, params = format_sql(s, [])
    assert res == ':name0 :name1::order_types :name2::json'
    assert not params


def test_parse_date_valid():
    s = '2022-01-24T05:00:00.000Z'
    res = try_parse_date(s)
    assert res


def test_parse_date_invalid():
    s = '2022-01-24'
    res = try_parse_date(s)
    assert not res


def test_get_cast_empty():
    res = get_cast("%s")
    assert res == ''


def test_get_cast_underscore():
    res = get_cast("%s::order_types")
    assert res == '::order_types'


def test_format_string_list():
    res = format_string_list("'1', '2', ''")
    assert res == "('1','2','')"


def test_unique_on_key():
    objs = [
        {'id': 1},
        {'id': 2},
        {'id': 2},
        None,
        {}
    ]

    result = unique_on_key(objs, 'id')
    ids = set(map(lambda x: x.get('id'), result))
    assert len(ids) == 2
    assert 1 in ids
    assert 2 in ids
