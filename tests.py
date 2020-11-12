from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from unittest import TestCase, main

from dataclass_as_config import (
    ArgumentError,
    ParseError,
    UnexpectedType,
    parse_config,
)


class TestParser(TestCase):
    def test_base(self) -> None:
        @dataclass(frozen=True)
        class Database:
            host: str
            port: int
            user: str
            password: str
            protocol: str
            database: str

        @dataclass(frozen=True)
        class Config:
            app_name: str
            database: Database

        config: Config = parse_config(
            data={
                'app_name': 'test',
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'user': 'postgres',
                    'password': 'root',
                    'protocol': 'postgres',
                    'database': 'postgres',
                },
            },
            expected=Config,
        )

        self.assertIsInstance(config, Config)
        self.assertIsInstance(config.database, Database)

    def test_unexpected_argument_error_shows_path(self) -> None:
        @dataclass(frozen=True)
        class LeafClass:
            final: str

        @dataclass(frozen=True)
        class NestedClass:
            name: str
            leaf: LeafClass

        @dataclass(frozen=True)
        class RootClass:
            name: str
            nested_param: NestedClass

        try:
            parse_config(
                data={
                    'name': 'test',
                    'nested_param': {
                        'name': 'my_app',
                        'leaf': {
                            'final': int,
                        },
                    },
                },
                expected=RootClass,
            )
        except ParseError as error:
            self.assertIn('".nested_param.leaf.final"', str(error))

    def test_simple_types_validation(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            name: int

        with self.assertRaises(UnexpectedType):
            parse_config(
                data={
                    'name': '1',
                },
                expected=TestClass
            )

        @dataclass(frozen=True)
        class TestClass:
            name: str

        with self.assertRaises(UnexpectedType):
            parse_config(
                data={
                    'name': 1,
                },
                expected=TestClass
            )

    def test_list(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            emails: list

        config = parse_config(
            data={
                'emails': ['email@email.com'],
            },
            expected=TestClass
        )
        self.assertIsInstance(config, TestClass)
        self.assertIsInstance(config.emails, list)
        self.assertEqual(config.emails, ['email@email.com'])

    def test_typed_list(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            emails: List[str]

        try:
            parse_config(
                data={
                    'emails': ['email@email.com', 2],
                },
                expected=TestClass
            )
        except UnexpectedType as error:
            self.assertEqual(
                str(error),
                '''".emails.1" contains <class 'int'> (2), but expected <class 'str'>'''
            )

    def test_typed_dict(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            counts: Dict[str, int]

        try:
            parse_config(
                data={
                    'counts': {
                        'Ann': '2',
                        'Bob': 1,
                    },
                },
                expected=TestClass
            )
        except UnexpectedType as error:
            self.assertEqual(
                str(error),
                "\".counts.Ann\" contains <class 'str'> ('2'),"
                " but expected <class 'int'>"
            )

    def test_deepcopy_list(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            emails: list

        data = {
            'emails': [
                ['email@email.com'],
            ],
        }
        config = parse_config(
            data=data,
            expected=TestClass
        )

        self.assertIsInstance(config, TestClass)
        self.assertIsInstance(config.emails, list)
        self.assertIsNot(config.emails[0], data['emails'][0])

    def test_deepcopy_dict(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            emails: dict

        data = {
            'emails': {
                'Ann': ['ann@email.com'],
            },
        }
        config = parse_config(
            data=data,
            expected=TestClass
        )

        self.assertIsInstance(config, TestClass)
        self.assertIsInstance(config.emails, dict)
        self.assertIsNot(config.emails['Ann'], data['emails']['Ann'])

    def test_optional(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            name: str
            age: Optional[int]

        data = {
            'name': 'Ann',
        }
        try:
            parse_config(
                data=data,
                expected=TestClass
            )
        except ArgumentError as error:
            self.assertEqual(error.path, '.age')
        else:
            self.fail('ArgumentError is not raised')

        @dataclass(frozen=True)
        class TestClass:
            name: str
            age: Optional[int] = None
            city: Optional[str] = 'London'
            height: Optional[int] = 20

        data = {
            'name': 'Ann',
            'height': 30,
        }

        config = parse_config(
            data=data,
            expected=TestClass
        )

        self.assertEqual(config.name, 'Ann')
        self.assertIsNone(config.age)
        self.assertEqual(config.city, 'London')
        self.assertEqual(config.height, 30)

    def test_union(self) -> None:
        @dataclass(frozen=True)
        class TestClass:
            name: str
            age: Union[int, str]

        data = {
            'name': 'Ann',
            'age': 20.0,
        }
        try:
            parse_config(
                data=data,
                expected=TestClass
            )
        except UnexpectedType as error:
            self.assertEqual(error.path, '.age')
            self.assertEqual(error.data, 20.0)
            self.assertEqual(error.expected, Union[int, str])
        else:
            self.fail('ArgumentError is not raised')

        data = {
            'name': 'Ann',
            'age': 30,
        }

        config = parse_config(
            data=data,
            expected=TestClass
        )

        self.assertEqual(config.name, 'Ann')
        self.assertEqual(config.age, 30)


class TestErrors(TestCase):
    def test_add_prefix(self) -> None:
        error = ParseError(path='.test.leaf')
        error.add_prefix('root')
        self.assertEqual(error.path, '.root.test.leaf')


if __name__ == '__main__':
    main()
