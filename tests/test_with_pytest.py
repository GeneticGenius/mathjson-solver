import sys
import os
import math
import pytest
import re

from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/"))

from mathjson_solver import (
    create_solver,
    MathJSONException,
    MathJSONDomainError,
    extract_variables,
)


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({}, ["Add", 2, 4, 3], 9),
        ({}, ["Sum", 2, 4, 3], 9),
        ({}, ["Sum", 2, 4, 3, None], 9),
        ({}, ["Add", 2, 4, "3"], 9),
        ({}, ["Sum", 2, 4, "3"], 9),
        ({}, ["Sum", 2, 4, "3", "abc"], 9),
        ({}, ["Sum", ["Array", 1, 1], 4, 3], 9),
        ({}, ["Sum", ["Array", 2, 4, 3]], 9),
        ({"a": 2}, ["Sum", "a", 4, 3], 9),
        ({"a": ["Array", 1, 1]}, ["Sum", "a"], 2),
        ({"a": ["Array", 1, 1]}, ["Sum", "a", 4, 3], 9),
        ({}, ["Subtract", 10, 5, 2], 3),
        ({}, ["Add", 5, 4, ["Negate", 3]], 6),
        ({}, ["Multiply", 2, 3, 4], 24),
        ({}, ["Divide", 10, 5], 2),
        ({}, ["Divide", 10, 4], 2.5),
        ({}, ["Rational", 10, 5], 2),
        ({}, ["Power", 2, 3], 8),
        ({}, ["Root", 9, 2], 3),
        ({}, ["Root", 8, 3], 2),
        ({}, ["Sqrt", 9], 3),
        ({}, ["Square", 4], 16),
        ({}, ["Round", ["Exp", 2], 3], 7.389),
        ({}, ["Divide", 10, ["Add", 2, 3]], 2),
        ({}, ["Round", ["Ln", 2.7183], 3], 1.0),
        ({}, ["Round", ["Log", 1000], 3], 3.0),
        ({}, ["Round", ["Ln", 2.7183, 12], 3], 1.0),
        ({}, ["Log2", 8], 3),
        ({}, ["Log10", 1000], 3),
    ],
)
def test_solver_arithmetics(parameters, expression, expected_result):
    solver = create_solver(parameters)
    assert solver(expression) == expected_result


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({}, ["Less", 10, 12], True),
        ({}, ["Less", 10, 12, 5], False),
        ({}, ["Less", 5, 12, 5], False),
        ({}, ["Less", 5, 12, 15], True),
        ({}, ["LessEqual", 12, 12, 15], True),
        ({}, ["LessEqual", 12, 12], True),
        ({}, ["LessEqual", 15, 12, 12], False),
        ({}, ["Greater", 10, 12], False),
        ({}, ["Greater", 10, 12, 5], False),
        ({}, ["Greater", 15, 12, 105], False),
        ({}, ["Greater", 5, 12, 5], False),
        ({}, ["Greater", 15, 12, 5], True),
        ({}, ["GreaterEqual", 15, 12, 12], True),
        ({}, ["GreaterEqual", 12, 12], True),
        ({}, ["GreaterEqual", 12, 12, 15], False),
        ({}, ["Equal", 10, 10], True),
        ({}, ["Equal", 10, 10, 15], False),
        ({}, ["Equal", 10, 12], False),
        ({}, ["NotEqual", 10, 10], False),
        ({}, ["NotEqual", 10, 10, 15], False),
        ({}, ["NotEqual", 10, 12], True),
        ({}, ["Equal", "aaa", "aaa"], True),
        ({}, ["Equal", "aaa", "baa"], False),
        ({}, ["Equal", "aaa", 11], False),
        ({}, ["Equal", None, "1"], False),
        ({}, ["Equal", 1, "1"], True),
        ({}, ["Greater", 1, 2], False),
        ({}, ["Greater", 2, -2], True),
        ({}, ["Greater", "2", -2], True),
        ({}, ["GreaterEqual", 1, 1], True),
        ({}, ["GreaterEqual", 2, 1], True),
        ({}, ["GreaterEqual", 2, "1"], True),
        ({}, ["GreaterEqual", 0, 0], True),
        ({}, ["GreaterEqual", 1, 2], False),
        ({}, ["Less", 1, 1], False),
        ({}, ["Less", 1, 2], True),
        ({}, ["LessEqual", 1, 1], True),
        ({}, ["LessEqual", 1, 2], True),
        # NotEqual
        ({}, ["NotEqual", 1, 1], False),
        ({}, ["NotEqual", 1, 2], True),
        ({}, ["NotEqual", "aaa", "bbb"], True),
        ({}, ["NotEqual", "aaa", 0], True),
    ],
)
def test_solver_comparison(parameters, expression, expected_result):
    solver = create_solver(parameters)
    assert solver(expression) == expected_result


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({}, ["Abs", -3.5], 3.5),
        ({}, ["Round", -5.123456, 2], -5.12),
        ({}, ["Round", -5.123456, 0], -5),
        ({}, ["Round", 5.4], 5),
        ({}, ["Round", 5.5], 6),
        ({}, ["Constants", ["a", 1], ["b", 2], "a"], 1),
        (
            {},
            ["Constants", ["a", 1], ["b", 2], ["c", 100], ["Sum", "a", "b"]],
            3,
        ),
        ({}, ["Constants", ["a", 1], ["b", ["Add", 2, "a"]], "b"], 3),
        ({"x": 1}, ["Add", 2, "x"], 3),
        ({"value": 1}, ["Switch", "value", 0, [1, 11], [2, 22]], 11),
        ({"value": 3}, ["Switch", "value", 0, [1, 11], [2, 22]], 0),
        (
            {"[uzwuoy][-1][14]": 1},
            ["Switch", "[uzwuoy][-1][14]", 0, [1, 11], [2, 22]],
            11,
        ),
        ({"14": 1}, ["Switch", "14", 0, [1, 11], [2, 22]], 11),
        ({"14": "1"}, ["Switch", "14", 0, ["0", 0], ["1", 1], ["2", 2]], 1),
        ({"29": "1"}, ["Switch", "29", 0, ["0", 0], ["1", 1], ["2", 2]], 1),
        ({"29": "2"}, ["Switch", "29", 0, ["0", 0], ["1", 1], ["2", 2]], 2),
        ({"a": "a"}, ["Switch", "a", 0, ["0", 0], ["1", 1], ["2", 2]], 0),
        (
            {"14": "1", "29": "1"},
            [
                "Add",
                ["Switch", "14", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "29", 0, ["0", 0], ["1", 1], ["2", 2]],
            ],
            2,
        ),
        ({}, ["Switch", "14", 6, ["0", 0], ["1", 1], ["2", 2]], 6),
        ({}, ["Switch", "1", 6, ["0", 0], ["1", 1], ["2", 2]], 1),  # BKUS
        (
            {"1": "2"},
            ["Switch", "1", 6, ["0", 0], ["1", 1], ["2", 2]],
            1,
        ),  # Because all "1"s become "2"
        (
            {"1": "3"},
            ["Switch", "1", 6, ["0", 0], ["1", 1], ["2", 2]],
            1,
        ),  # Because string "1" is equal string "1"
        (
            {
                "14": "1",
                "29": "1",
                "30": "1",
                "31": "1",
                "32": "1",
                "33": "1",
                "35": "1",
                "45": "1",
                "50": "1",
                "52": "1",
                "71": "1",
                "91": "1",
                "112": "1",
            },
            [
                "Add",
                ["Switch", "14", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "29", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "30", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "31", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "32", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "33", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "35", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "45", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "50", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "52", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "71", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "91", 0, ["0", 0], ["1", 1], ["2", 2]],
                ["Switch", "112", 0, ["0", 0], ["1", 1], ["2", 2]],
            ],
            13,
        ),
        # The next tests check the type-forgiving nature of Switch.
        ({"value": 2}, ["Switch", "value", 0, ["1", 11], ["2", 22]], 22),
        ({"value": "2"}, ["Switch", "value", 0, [1, 11], [2, 22]], 22),
        # The next tests verify that the StrictSwitch is not forgiving.
        ({"value": 2}, ["StrictSwitch", "value", 0, ["1", 11], ["2", 22]], 0),
        ({"value": "2"}, ["StrictSwitch", "value", 0, [1, 11], [2, 22]], 0),
        (
            {"color": "red"},
            ["Switch", "color", 0, ["blue", 10], ["red", 30]],
            30,
        ),
        (
            {"color": "green"},
            ["Switch", "color", 0, ["blue", 10], ["red", 30]],
            0,
        ),
        (
            {"color": "green"},
            ["Switch", "undefined", 0, ["blue", 10], ["red", 30]],
            0,
        ),
        ({}, ["If", [["Equal", 1, 0], 10], [["Equal", 2, 2], 20], 9000], 20),
        # # The following tests that If don't fail on incompatible data types
        (
            {"a": 1},
            ["If", [["Equal", "a", 1], 10], [["Equal", "a", "1"], 20], -1],
            10,
        ),
        ({"a": 10, "b": 10}, ["If", [["Equal", "a", "b"], 10], 9000], 10),
        ({"a": 10, "b": 20}, ["If", [["Equal", "a", "b"], 10], 9000], 9000),
        ({"a": 10}, ["If", [["Equal", "a", "b"], 10], 9000], 9000),
        # The following test checks if Sum failure (1+"b") is handled correctly in If.
        ({"a": 10}, ["If", [["Equal", "a", ["Sum", 1, "b"]], 10], 9000], 9000),
        ({}, ["Array", 1, 2, 3, 5, 2], ["Array", 1, 2, 3, 5, 2]),
        ({}, ["Max", ["Array", 1, 2, 3, 5, 2]], 5),
        ({}, ["Max", ["Array", 1, 2, ["Sum", 2, 4, 3], 5, 2]], 9),
        ({"a": ["Array", 1, 2, 3, 5, 2]}, ["Max", "a"], 5),
        ({}, ["Min", ["Array", 1, 2, 3, 5, 2]], 1),
        ({"a": ["Array", 2, 1, 3, 5, 2]}, ["Min", "a"], 1),
        ({}, ["Median", ["Array", 1, 2, 3, 5, 2]], 2),
        ({"a": ["Array", 1, 2, 3, 5, 2]}, ["Median", "a"], 2),
        ({}, ["Average", ["Array", 2, "three", 4, "6"]], 4),
        ({}, ["Average", ["Array", 1, 2, 3, 5, 2]], 2.6),
        (
            {},
            [
                "Average",
                [
                    "Array",
                    "-2",
                    -1,
                    "0",
                    1,
                    "2",
                    "3",
                    4,
                    5,
                    6,
                    "seven",
                    8,
                    "9",
                    "10",
                    15,
                    10,
                ],
            ],
            5.0,
        ),
        ({}, ["Average", ["Array"]], None),
        ({"a": ["Array", 2, 8]}, ["Average", "a"], 5),
        ({"a": 10, "b": 20}, ["Average", ["Array", "a", "b"]], 15),
        ({}, ["Length", ["Array", 1, 2, 3, 5, 2, 9]], 6),
        ({}, ["Length", ["Array", 1, 2, 3, None]], 4),
        ({"a": ["Array", 1, 2, 3, 5, 2, 9]}, ["Length", "a"], 6),
        ({}, ["Length", ["Array"]], 0),
        # Next test illustrates an invalid formula, where 'Length' receives an invalid array.
        ({}, ["Length", ["Greater", ["Array", 3, 5, 6, 4, 8, 1, 0, 1], 5]], 2),
        ({}, ["Sum", ["Array", True, False, True, False, False]], 2),
        ({}, ["Int", "12"], 12),
        ({}, ["Int", "12.2"], 12),
        ({}, ["Float", "12.2"], 12.2),
        (
            {},
            ["Date", "2025-11-05T17:28:01"],
            datetime(2025, 11, 5, 17, 28, 1),
        ),
        (
            {},
            ["Date", "2025-07-21 10:30:45"],
            datetime(2025, 7, 21, 10, 30, 45),
        ),
        (
            {},
            ["Date", "2025-11-05"],
            datetime(2025, 11, 5),
        ),
        (
            {},
            ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
            datetime(2025, 1, 10, 10, 5),
        ),
        ({}, ["Any", ["Array", 0, 0, False, 0, 0]], False),
        ({}, ["Any", ["Array", 0, 1, False, 0, 0]], True),
        ({}, ["All", ["Array", 0, 1, False, 0, 0]], False),
        ({}, ["All", ["Array", 0, 1, False, "", 0]], False),
        ({}, ["All", ["Array", 2, 1, True, "zz", 2]], True),
        ({}, ["Str", 12], "12"),
        ({}, ["Str", "12"], "12"),
        ({}, ["Str", "aabb"], "aabb"),
        ({}, "aabb", "aabb"),
        ({}, 11, 11),
        ({}, True, True),
        ({}, False, False),
        ({}, ["In", 2, ["Array", 1, 2, 3]], True),
        ({}, ["In", 4, ["Array", 1, 2, 3]], False),
        ({}, ["In", "Abc", ["Array", 1, 2, "Abc", 4]], True),
        ({}, ["In", "Abc", ["Array", 1, 2, "Abcd", 4]], False),
        ({}, ["In", ["Add", 2, 2], ["Array", 1, 4, 3]], True),
        ({}, ["In", ["Add", 2, 1], ["Array", 1, 2, ["Add", 1, 2]]], True),
        (
            {"a": 10, "b": 20},
            ["In", ["Add", "a", "b"], ["Array", 1, 2, ["Add", 15, 15], 4]],
            True,
        ),
        (
            {"a": 10, "b": 20},
            ["In", ["Add", "a", "b"], ["Array", 1, 2, ["Add", 15, 16], 4]],
            False,
        ),
        ({"a": [10, 20, 30]}, ["In", 20, "a"], True),
        ({"a": [10, 20, 30]}, ["In", 21, "a"], False),
        ({}, ["Not_in", 2, ["Array", 1, 2, 3]], False),
        ({}, ["Not_in", 4, ["Array", 1, 2, 3]], True),
        ({}, ["NotIn", 4, ["Array", 1, 2, 3]], True),
        ({"a": [10, 20, 30]}, ["Not_in", 20, "a"], False),
        ({"a": [10, 20, 30]}, ["Not_in", 21, "a"], True),
        (
            {},
            ["Contains_any_of", ["Array", 1, 2, 3], ["Array", 1, 2, 3]],
            True,
        ),
        ({}, ["Contains_any_of", ["Array", 2, 3], ["Array", 1, 2]], True),
        (
            {},
            ["Contains_any_of", ["Array", 1, 2, 3], ["Array", 3, 4, 5, 6]],
            True,
        ),
        (
            {},
            ["Contains_any_of", ["Array", 1, 2, 3], ["Array", 4, 5, 6]],
            False,
        ),
        (
            {},
            [
                "Contains_any_of",
                ["Array", 1, ["Add", 1, 1], 6],
                ["Array", 4, 5, ["Add", 3, 3]],
            ],
            True,
        ),
        (
            {},
            [
                "Contains_any_of",
                ["Array", 1, ["Add", 1, 1], 3],
                ["Array", 4, 5, ["Add", 3, 3]],
            ],
            False,
        ),
        (
            {"a": [10, 20, 30]},
            ["Contains_any_of", "a", ["Array", 1, 20, 3]],
            True,
        ),
        (
            {"b": [1, 20, 3]},
            ["Contains_any_of", ["Array", 1, 2, 3], "b"],
            True,
        ),
        ({"b": [1, 20, 3]}, ["ContainsAnyOf", ["Array", 1, 2, 3], "b"], True),
        (
            {"a": [10, 20, 30], "b": [1, 20, 3]},
            ["Contains_any_of", "a", "b"],
            True,
        ),
        (
            {"a": [10, 20, 30], "b": [1, 2, 3]},
            ["Contains_any_of", "a", "b"],
            False,
        ),
        (
            {},
            ["Contains_all_of", ["Array", 1, 2, 3], ["Array", 1, 2, 3]],
            True,
        ),
        ({}, ["Contains_all_of", ["Array", 1, 2], ["Array", 1, 2, 3]], False),
        ({}, ["Contains_all_of", ["Array", 1, 2, 3], ["Array", 1, 2]], True),
        ({}, ["Contains_all_of", ["Array", 1, 2, 3], ["Array", 2]], True),
        ({}, ["ContainsAllOf", ["Array", 1, 2, 3], ["Array", 2]], True),
        (
            {"a": [10, 20, 30], "b": [1, 20, 3]},
            ["Contains_all_of", "a", "b"],
            False,
        ),
        ({"a": [1, 2, 3], "b": [1, 2]}, ["Contains_all_of", "a", "b"], True),
        (
            {},
            ["Contains_none_of", ["Array", 1, 2, 3], ["Array", 1, 2, 3]],
            False,
        ),
        ({}, ["Contains_none_of", ["Array", 1, 2], ["Array", 2, 3]], False),
        ({}, ["ContainsNoneOf", ["Array", 1, 2], ["Array", 2, 3]], False),
        ({}, ["Contains_none_of", ["Array", 1, 2, 3], ["Array", 4, 5]], True),
        ({}, ["Not", True], False),
        ({}, ["Not", 0], True),
        ({}, ["Not", ["In", 2, ["Array", 1, 2, 3]]], False),
        ({}, ["Array", 2, 4, 3], ["Array", 2, 4, 3]),
        (
            {},
            ["StrictMap", ["Array", 1, 2, 3], ["Square"]],
            ["Array", 1, 4, 9],
        ),
        (
            {},
            ["Filter", ["Array", 1, 2, 3], ["LessEqual"], 2],
            ["Array", 1, 2],
        ),
        (
            {},
            ["Filter", ["Array", 1, 2, 3, "None"], ["LessEqual"], 2],
            ["Array", 1, 2],
        ),
        ({}, ["Map", ["Array", 1, 2, 3], ["Square"]], ["Array", 1, 4, 9]),
        (
            {},
            ["Map", ["Array", 1, 2, 3, None, "a"], ["Square"]],
            ["Array", 1, 4, 9, None, "a"],
        ),
        ({}, ["Map", ["Array", 1, 2, 3], ["Power"], 2], ["Array", 1, 4, 9]),
        (
            {},
            ["Map", ["Array", 1, 2, 3], ["GreaterEqual"], 2],
            ["Array", False, True, True],
        ),
        (
            {},
            [
                "Sum",
                [
                    "Map",
                    ["Array", 1, 2, 3, 4, 1, 1, 0, 1],
                    ["GreaterEqual"],
                    2,
                ],
            ],
            3,
        ),
        ({}, ["Sum", ["Array", True, False, True, False, False]], 2),
        # ["HasMatchingSublist", list, required_match_count, position, contiguous, function, more parameters]
        (
            {},
            [
                "HasMatchingSublist",
                ["Array", 1, 2, 3, 4, 5, 6],
                3,
                0,
                True,
                ["GreaterEqual"],
                1,
            ],
            True,  # first 3 elements are greater than 3
        ),
        (
            {},
            [
                "HasMatchingSublist",
                ["Array", 1, 2, 3, 4, 5, 6],
                3,
                0,
                True,
                ["GreaterEqual"],
                2,
            ],
            False,  # first 3 elements are greater than 3 - False
        ),
        (
            {},
            [
                "HasMatchingSublist",
                ["Array", 1, 2, 3, 4, 5, 6],
                3,
                0,
                False,  # anywhere
                ["GreaterEqual"],
                4,
            ],
            True,
        ),
        (
            {},
            [
                "HasMatchingSublist",
                ["Array", 1, 2, 3, 4, 5, 6],
                4,
                0,
                False,  # anywhere
                ["GreaterEqual"],
                4,
            ],
            False,
        ),
        (
            {},
            [
                "HasMatchingSublist",
                ["Array", 1, 2, 3, 4, 5, 6],
                3,
                -1,
                True,
                ["GreaterEqual"],
                4,
            ],
            True,
        ),
        (
            {},
            [
                "HasMatchingSublist",
                ["Array", 1, 2, 3, 4, 5, 6],
                5,
                -1,
                True,
                ["GreaterEqual"],
                4,
            ],
            False,
        ),
        (
            {},
            [
                "Strftime",
                ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
                "%Y",
            ],
            "2025",
        ),
        ({}, ["Strftime", ["Today"], "%Y"], "2026"),
        ({}, ["Strftime", ["Now"], "%Y"], "2026"),
        (
            {},
            [
                "Strftime",
                [
                    "Add",
                    ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
                    ["TimeDeltaDays", 3],
                ],
                "%d",
            ],
            "13",
        ),
        (
            {},
            [
                "Strftime",
                [
                    "Subtract",
                    ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
                    ["TimeDeltaDays", 3],
                ],
                "%d",
            ],
            "07",
        ),
        (
            {},
            [
                "Strftime",
                [
                    "Add",
                    ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
                    ["TimeDeltaMinutes", 5],
                ],
                "%M",
            ],
            "10",
        ),
        (
            {},
            [
                "Strftime",
                [
                    "Add",
                    ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
                    ["TimeDeltaHours", 2],
                ],
                "%H",
            ],
            "12",
        ),
        (
            {},
            [
                "Strftime",
                [
                    "Add",
                    ["Strptime", "2025-01-10T10:05", "%Y-%m-%dT%H:%M"],
                    ["TimeDeltaWeeks", 1],
                ],
                "%d",
            ],
            "17",
        ),
    ],
)
def test_solver_simple(parameters, expression, expected_result):
    solver = create_solver(parameters)
    assert solver(expression) == expected_result


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({}, ["Log", 100], pytest.approx(2)),
        ({}, ["Log", 1], pytest.approx(0)),
        ({}, ["Log", 0.001], pytest.approx(-3)),
        ({}, ["Log", 8, 2], pytest.approx(3)),
        ({}, ["Ln", "ExponentialE"], pytest.approx(1)),
        ({"ExponentialE": 10}, ["Add", "ExponentialE", 1], 11),
        ({}, ["Constants", ["ExponentialE", 3], "ExponentialE"], 3),
        ({}, ["Power", 10, 2], 100),
        ({}, ["Power", 10, 0], 1),
        ({}, ["Power", 10, -3], pytest.approx(0.001)),
        ({}, ["Power", -2, 3], -8),
        ({}, ["Root", 27, 3], 3),
        ({}, ["Root", -8, 3], -2),
        ({}, ["Root", -27, 3], -3),
        ({}, ["Root", -32, 5], -2),
        ({}, ["Root", -8, 3.0], -2),
    ],
)
def test_solver_log_power_root(parameters, expression, expected_result):
    solver = create_solver(parameters)
    assert solver(expression) == expected_result


@pytest.mark.parametrize(
    "expression, inner_exception",
    [
        (["Log", 0], MathJSONDomainError),
        (["Log", -5], MathJSONDomainError),
        (["Log", 8, 1], MathJSONDomainError),
        (["Log", 8, 0], MathJSONDomainError),
        (["Log", 8, -2], MathJSONDomainError),
        (["Ln", 0], MathJSONDomainError),
        (["Log2", -1], MathJSONDomainError),
        (["Log10", 0], MathJSONDomainError),
        (["Sqrt", -4], MathJSONDomainError),
        (["Root", -16, 4], MathJSONDomainError),
        (["Root", -8, 2.5], MathJSONDomainError),
        (["Power", -8, 0.333], MathJSONDomainError),
        (["Power", 10, 400], OverflowError),
        (["Power", 0, -1], ZeroDivisionError),
        (["Multiply", 1e300, 1e300], OverflowError),
        (["Exp", 1000], OverflowError),
    ],
)
def test_raises_domain_and_overflow(expression, inner_exception):
    solver = create_solver({})
    with pytest.raises(MathJSONException) as exc_info:
        solver(expression)
    assert isinstance(exc_info.value.e, inner_exception)


@pytest.mark.parametrize(
    "expression, expected_result",
    [
        (["Root", 27, 3], 3),
        (["Root", -27, 3], -3),
        (["Root", 26, 3], 3.0000000000000004),
    ],
)
def test_root_is_exact_when_cbrt_is_one_ulp_off(
    monkeypatch, expression, expected_result
):
    # glibc's cbrt, as on Linux, answers 3.0000000000000004 for 27
    monkeypatch.setattr(math, "cbrt", lambda x: 3.0000000000000004)
    assert create_solver({})(expression) == expected_result


def test_domain_error_is_value_error():
    assert issubclass(MathJSONDomainError, ValueError)


def test_unknown_head_strict():
    assert create_solver({})(["Sin", 1]) == ["Sin", 1]
    assert create_solver({}, strict=False)(["Sin", 1]) == ["Sin", 1]
    solver = create_solver({}, strict=True)
    with pytest.raises(MathJSONException) as exc_info:
        solver(["Sin", 1])
    assert isinstance(exc_info.value.e, NotImplementedError)
    assert exc_info.value.construct == "Sin"
    with pytest.raises(MathJSONException):
        solver(["Add", 1, ["Sin", 1]])


def test_known_heads_in_strict_mode():
    solver = create_solver({"a": ["Array", 1, 2, 3]}, strict=True)
    assert solver(["Map", ["Array", 1, 2, 3], ["Square"]]) == [
        "Array",
        1,
        4,
        9,
    ]
    assert solver(["StrictMap", "a", ["Power"], 2]) == ["Array", 1, 4, 9]
    assert solver(["Filter", "a", ["Greater"], 1]) == ["Array", 2, 3]
    assert solver(["Sum", "a"]) == 6
    assert solver(["Max", "a"]) == 3
    assert solver(["Round", ["Log", 1000], 3]) == 3.0


def test_raises_divide():
    solver = create_solver({})
    with pytest.raises(
        MathJSONException,
        match=re.escape(
            "Problem in Divide. ['Divide', 1, 0]. division by zero"
        ),
    ):
        solver(["Divide", 1, 0])


def test_raises_malformed():
    solver = create_solver({})
    with pytest.raises(
        MathJSONException,
        match=re.escape(
            "Problem in Power. ['Power', 1]. list index out of range"
        ),
    ):
        solver(["Power", 1])


def test_handle_exception():
    solver = create_solver({})
    try:
        solver(["Power", 1])
    except MathJSONException:
        assert True
    else:
        assert False


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({}, ["Add", 2, 4, 3], set()),
        ({}, ["Sum", 2, "a", 3], set(["a"])),
        ({"a": 5}, ["Sum", 2, "a", 3], set()),
        ({"a": 5, "b": 6}, ["Sum", 2, "a", "c"], set(["c"])),
        ({}, ["Constants", ["c", 1], ["d", ["Add", 2, "a"]], "d"], set(["a"])),
        # Now with "ugly" variables that mimic the ones used for deep referencing.
        (
            {},
            [
                "Add",
                "[slug1][0][question1]",
                "y",
                4,
                "[slug1][-3:-1][question1]",
            ],
            set(["[slug1][0][question1]", "y", "[slug1][-3:-1][question1]"]),
        ),
        (
            {},
            ["If", [["Equal", "[uzwuoy][-1][question1]", 200], 200], 1],
            set(["[uzwuoy][-1][question1]"]),
        ),
        (
            {},
            [
                "If",
                [["Equal", "[uzwuoy][-1][question1]", 200], 201],
                [["Equal", "[uzwuoy][-2][question1]", 100], 101],
                1,
            ],
            set(["[uzwuoy][-1][question1]", "[uzwuoy][-2][question1]"]),
        ),
    ],
)
def test_extract_variables(parameters, expression, expected_result):
    assert (
        extract_variables(
            expression, set(), set([x for x in parameters.keys()])
        )
        == expected_result
    )
