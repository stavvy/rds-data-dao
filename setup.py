from setuptools import setup

setup(name='rds_data_dao',
      version='0.1.9',
      description='RDS Data API Wrapper',
      url='https://github.com/stavvy/rds-data-dao',
      author='Chris Buonocore',
      author_email='chris@stavvy.com',
      license='MIT',
      test_suite='tests',
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      packages=['rds_data_dao'],
      zip_safe=False)