```python
>>> from dataclass_as_config import parse_config
... from dataclasses import dataclass
... 
... 
... @dataclass(frozen=True)
... class Database:
...     host: str 
...     port: int 
...     user: str 
...     password: str 
...     protocol: str 
...     database: str 
... 
... @dataclass(frozen=True)
... class Config:
...     app_name: str
...     database: Database
... 
... config: Config = parse_config(
...     data={
...         'app_name': 'test',
...         'database': {
...             'host': 'localhost',
...             'port': 5432,
...             'user': 'postgres',
...             'password': 'root',
...             'protocol': 'postgres',
...             'database': 'postgres',
...         },
...     },
...     expected=Config,
... )
>>> print(conifg)
Config(app_name='test', database=Database(host='localhost', port=5432, user='postgres', password='root', protocol='postgres', database='postgres'))


```
