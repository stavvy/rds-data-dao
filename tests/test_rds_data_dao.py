import pytest
from unittest import mock
from rds_data_dao import RdsDataDao

# Example RDS Data API Response.
TEST_RESPONSE = {
    "numberOfRecordsUpdated": 0,
    "columnMetadata": [
        {
            "name": "id"
        },
        {
            "name": "name"
        }],
    "records": [
        [
            {
                "longValue": 1
            },
            {
                "stringValue": "John"
            }
        ],
        [
            {
                "longValue": 2
            },
            {
                "stringValue": "Joe"
            }
        ]
    ]
}


def test_dao_str():
    dao = RdsDataDao('mydb', 'mycluster', 'mysecret')
    assert str(dao) == 'RdsDataDao: mydb mycluster'


def test_dao_returns_json_response():
    dao = RdsDataDao('mydb', 'mycluster', 'mysecret')
    dao.rds_data = mock.MagicMock()
    dao.rds_data.execute_statement.return_value = TEST_RESPONSE
    result = dao.get("select * from table", [])
    assert result == [{"id": 1, "name": "John"}, {"id": 2, "name": "Joe"}]
