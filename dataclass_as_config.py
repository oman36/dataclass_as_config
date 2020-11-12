from copy import deepcopy
import dataclasses
from dataclasses import dataclass, fields, is_dataclass
import typing
from typing import Any, Type


@dataclass
class ParseError(Exception):
    path: str

    def add_prefix(self, path: str) -> None:
        path = f'.{path}'
        if self.path:
            self.path = f'{path}{self.path}'
        else:
            self.path = path


@dataclass
class ArgumentError(ParseError, TypeError):
    expected: Type
    msg: str

    def __str__(self):
        return f'{self.msg} for {self.expected} at "{self.path}"'


@dataclass
class UnexpectedType(ParseError):
    expected: Type
    data: Any

    def __str__(self):
        return f'"{self.path}" contains {type(self.data)} ({self.data!r}), ' \
               f'but expected {self.expected}'


def parse_config(data: Any, expected: Type) -> Any:
    if is_dataclass(expected):
        if not isinstance(data, dict):
            raise UnexpectedType(path='', data=data, expected=expected)
        data = data.copy()
        for field in fields(expected):
            is_not_required_field = (
                    not isinstance(field.default, dataclasses._MISSING_TYPE)
                    or
                    not isinstance(field.default_factory, dataclasses._MISSING_TYPE)
            )
            if is_not_required_field and field.name not in data:
                continue
            if field.name not in data:
                raise ArgumentError(f'.{field.name}', field.type, 'Argument missed')
            try:
                data[field.name] = parse_config(
                    data=data.pop(field.name),
                    expected=field.type,
                )
            except ParseError as error:
                error.add_prefix(field.name)
                raise error from error
        try:
            return expected(**data)
        except TypeError as error:
            raise ArgumentError('', expected, error.args[0]) from error

    elif expected.__class__ is typing._GenericAlias and expected.__origin__ is dict:
        key_type, value_type = expected.__args__
        if not isinstance(data, dict):
            raise UnexpectedType('', expected, data)
        result = {}
        for key, value in data.items():
            try:
                result[key] = parse_config(value, value_type)
            except ParseError as error:
                error.add_prefix(key)
                raise error from error
        return result
    elif expected is dict:
        if not isinstance(data, dict):
            raise UnexpectedType('', expected, data)
        return deepcopy(data)
    elif expected.__class__ is typing._GenericAlias and expected.__origin__ is list:
        if not isinstance(data, list):
            raise UnexpectedType('', expected, data)
        klass = expected.__args__[0]
        result = []
        for i, value in enumerate(data):
            try:
                result.append(parse_config(value, klass))
            except ParseError as error:
                error.add_prefix(str(i))
                raise error from error
        return result
    elif expected is list:
        if not isinstance(data, list):
            raise UnexpectedType('', expected, data)
        return deepcopy(data)
    elif expected.__class__ is typing._GenericAlias and \
            expected.__origin__ is typing.Union:
        for type_ in expected.__args__:
            if isinstance(data, type_):
                return data
        raise UnexpectedType('', expected, data)

    elif not isinstance(data, expected):
        raise UnexpectedType('', expected, data)
    return data
