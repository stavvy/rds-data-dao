import json

import boto3
import os
import logging

from .db_util import format_sql, render_data_api_response


class RdsDataDao:

    def __init__(self, db, cluster_arn=None, secret_arn=None, **kwargs):
        self.db = db
        self.cluster_arn = cluster_arn or os.getenv('DB_URL')
        self.secret_arn = secret_arn or os.getenv('DB_CREDENTIALS')
        self.logger = logging.getLogger(kwargs.get('logger_name', db))
        endpoint_url = os.getenv('DB_ENDPOINT_URL', None)
        if endpoint_url:
            self.rds_data = boto3.client('rds-data', endpoint_url=endpoint_url)
        else:
            self.rds_data = boto3.client('rds-data')

    def __str__(self):
        return '{}: {} {}'.format(self.__class__.__name__, self.db, self.cluster_arn)

    def insert(self, cmd, data=None, multiple_returns=False):
        items = self._execute(cmd, True, data=data)
        return self.get_first(items) if not multiple_returns else items

    def get(self, cmd, data=None):
        return self._execute(cmd, data=data)

    def get_objects(self, cmd, parsing_class, data=None):
        return [parsing_class.parse_obj(item) for item in self._execute(cmd, data=data)]

    def delete(self, cmd, data=None):
        self._execute(cmd, False, data)

    def get_single_result(self, cmd, data=None):
        result = self._execute(cmd, data=data)
        return self.get_first(result)

    def get_single_result_object(self, cmd, parsing_class, data=None):
        result = self._execute(cmd, data=data)
        single_result = self.get_first(result)
        if single_result:
            return parsing_class.parse_obj(single_result)
        return None

    def update(self, cmd, data=None):
        return self._execute(cmd, True, data=data)

    def transaction_begin(self):
        response = self.rds_data.begin_transaction(resourceArn=self.cluster_arn,
                                                   secretArn=self.secret_arn,
                                                   database=self.db)
        if 'transactionId' not in response:
            raise Exception('No transaction id found in response', response)
        transaction_id = response['transactionId']
        self.logger.debug('tx ' + str(transaction_id))
        return transaction_id

    def get_first(self, items):
        return items[0] if (items and len(items) > 0) else None

    def transaction_insert(self, transaction_id, cmd, data=None):
        self.logger.debug('tx ' + str(transaction_id))
        try:
            items = self._execute(cmd, True, data=data, transaction_id=transaction_id)
            return self.get_first(items)
        except Exception as e:
            print(f'Error: {e}')
            self.rds_data.rollback_transaction(resourceArn=self.cluster_arn,
                                               secretArn=self.secret_arn, transactionId=transaction_id)
            raise e

    def transaction_end(self, transaction_id):
        self.logger.debug('tx ' + str(transaction_id))
        try:
            self.rds_data.commit_transaction(resourceArn=self.cluster_arn,
                                             secretArn=self.secret_arn, transactionId=transaction_id)
        except Exception as e:
            print(f'Error: {e}')
            self.rds_data.rollback_transaction(resourceArn=self.cluster_arn,
                                               secretArn=self.secret_arn, transactionId=transaction_id)
            raise e

    def _execute(self, cmd, insert=False, data=None, transaction_id=''):
        if not cmd:
            return
        will_return = not insert or 'returning' in cmd.lower()
        sql, parameters = format_sql(cmd, data)
        self.logger.debug('query: %s' % {'sql': sql, 'parameters': json.dumps(parameters)})
        try:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds-data.html#RDSDataService.Client.execute_statement
            response = self.rds_data.execute_statement(
                resourceArn=self.cluster_arn,
                secretArn=self.secret_arn,
                database=self.db,
                includeResultMetadata=True,
                resultSetOptions={
                    'decimalReturnType': 'STRING'
                },
                transactionId=transaction_id,
                parameters=parameters,
                sql=sql)
            return render_data_api_response(response).get('records', None) if will_return else None
        except Exception as e:
            self.logger.error('error executing command: %s' % {'cmd': cmd}, exc_info=e)
            raise e
