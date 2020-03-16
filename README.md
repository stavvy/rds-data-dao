# RdsDataDao
---

A wrapper around the RDS Data API offering query escaping and automatic parameterization.


### Example usages.

1. Provide cmd and data arguments to the crud methods on the RdsDataDao object. 
It will automatically cast and convert the arguments to parameterized form.

2. Use %s for any parameterized argument (except arrays).

2. Use %s::type to cast arguments, for example %s::json, will cast the argument to json.

ex usage:

<pre>
def get_bank():
    cmd = "select * from banks where id = %s"
    data = [bank_id]
    bank = self.get_single_result(cmd, data)
    return bank
</pre>

For arrays, `make_list` from `db_util` should be used as arrays are not natively parameterizable as of this writing in the RDS Data API.

<pre>
    cmd = "select bank_id from files where id in {}".format(make_list(ids)) # ids is list of integers here.
    banks = self._get(cmd)
    return banks
</pre>

### Example Response

The RdsDataDao translates responses into dict format using returned column definitions in the data api:

<pre>
{
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
</pre>

maps to:

<pre>
[
    {"id": 1, "name": "John"}, 
    {"id": 2, "name": "Joe"}
]
</pre>


### References
<!-- https://medium.com/@bfortuner/python-unit-testing-with-pytest-and-mock-197499c4623c -->
<!-- https://github.com/lyft/python-blessclient/blob/master/tests/blessclient/bless_lambda_test.py --> 
