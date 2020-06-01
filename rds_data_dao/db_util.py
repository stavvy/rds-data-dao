import itertools as it
import json
import re
from datetime import datetime
from urllib import parse


def safe_escape_string(s):
    # Filter nonstandard characters from input, need to fix for complex object/json inputs.
    return re.sub('[^-|.:_A-Za-z0-9 ]+', '', str(s))


def _render_value(value):
    if value.get("isNull"):
        return None
    elif "arrayValue" in value:
        if "arrayValues" in value["arrayValue"]:
            return [_render_value(nested) for nested in value["arrayValue"]["arrayValues"]]
        else:
            return list(value["arrayValue"].values())[0]
    else:
        return list(value.values())[0]


def parse_db_timestamp(d):
    if type(d) == str:
        d = datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f')
    return datetime.timestamp(d)


def render_data_api_response(response):
    if "records" in response:
        column_names = list(map(lambda x: x['name'], response.get('columnMetadata', [])))
        print(column_names, response['records'])
        for i, record in enumerate(response["records"]):
            response["records"][i] = {column_names[j]: _render_value(v) for j, v in enumerate(response["records"][i])}
    return response


DATA_API_TYPE_MAP = {
    bytes: "blobValue",
    dict: "stringValue",
    bool: "booleanValue",
    float: "doubleValue",
    int: "longValue",
    str: "stringValue",
    list: "arrayValue",
    tuple: "arrayValue"
}


def get_data_type(x):
    return DATA_API_TYPE_MAP.get(type(x), 'stringValue')


def is_json(myjson):
    if type(myjson) == 'str':
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
    return True


# ex: x::org_types -> org_types
def get_cast(format_match):
    return format_match[2:]


# ref: https://github.com/chanzuckerberg/aurora-data-api
# https://aws.amazon.com/blogs/database/using-the-data-api-to-interact-with-an-amazon-aurora-serverless-mysql-database/
# https://forums.aws.amazon.com/thread.jspa?messageID=921843
def format_sql(raw_sql, data):
    # using parameterized str for now.
    if not data:
        data = []
    data = tuple(map(stringify_for_data_api_query, data))

    def parameterize_string(s):
        cnt = it.count()
        return re.sub(r"(%s[a-zA-Z_:]*)", lambda x: ':name{}{}'.format(next(cnt), get_cast(x.group(0))), s)

    sql = parameterize_string(raw_sql)

    print('parameter sql', sql)

    def create_parameter(i, v):
        value_type = get_data_type(v)
        value = {value_type: v}
        if value_type == 'arrayValue':
            if v:
                element_type = '{}s'.format(get_data_type(v[0]))
            else:
                element_type = 'stringValues'
            value[value_type] = {element_type: v}
        elif v is 'null':
            value = {'isNull': True}

        return {'name': 'name{}'.format(i), 'value': value}

    parameters = [create_parameter(i, v) for i, v in enumerate(data)]
    return sql, parameters


def remove_special(s):
    return re.sub(r'[^a-zA-Z0-9]+', ' ', s)


def quote_escape(x):
    return parse.quote(str(x), '| @:')


def try_parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")
    except:
        return None


def stringify_for_data_api_query(x, manual_escape=False):
    type_x = type(x)

    if type_x in (bool, list, tuple, bytes, float, int):
        return x
    elif type_x is dict:
        return json.dumps(x)
    elif x is None:
        return 'null'

    if manual_escape:
        v = try_parse_date(x)
        if v:
            return str(v)
        return quote_escape(x)

    # Default to string.
    return str(x)


def make_list(items):
    return '({})'.format(','.join(map(lambda x: "'{}'".format(stringify_for_data_api_query(x, True)), items)))


# Convert comma separated list of items as string to escaped sql string list format
# ex: "'1', '2'" => ('1', '2')
def format_string_list(s):
    return make_list(re.sub("['\" ]", "", s).split(','))


# select unique items filtering nulls
def unique_on_key(elements, key):
    return list({element.get(key): element for element in elements if element and key in element}.values())


# https://realpython.com/prevent-python-sql-injection/
def create_update_clause(obj):
    clause = []
    for k, v in obj.items():
        k = quote_escape(k)
        if v is None:
            clause.append("{}=null".format(k))
        else:
            clause.append("{}='{}'".format(k, stringify_for_data_api_query(escape_percent(v), True)))
    if not clause:
        return ''

    return ', '.join(clause)

    # https://stackoverflow.com/questions/40230546/python-string-percent-sign-escape/40230658
    def escape_percent(self, value):
        return value.replace('%', '%%') if isinstance(value, str) else value
