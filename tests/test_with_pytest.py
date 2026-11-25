import sys
import os
import math
import pytest
import re

from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../src/"))

from mathjson_solver import (
    create_solver,
    MathJSONDomainError,
    MathJSONException,
    MathJSONOverflowError,
    MathJSONUnderflowError,
    MathJSONUnresolvedParameter,
    MathJSONUnsupportedOperator,
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
        ({}, ["Round", ["Log", 2.7183], 3], 1.0),
        ({}, ["Round", ["Ln", 2.7183], 3], 1.0),
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
        ({}, ["Constants", ["x", 5], ["Add", "x", "y"]], set(["y"])),
        ({}, ["Equal", "a", ["Str", "NEEDS_REVIEW"]], set(["a"])),
        ({}, ["Less", "a", ["Date", "2026-01-01"]], set(["a"])),
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


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({"a": 3000}, ["Add", "a", "b"], 3000.0),
        ({}, ["Add", "a", "b"], "ab"),
        ({"a": 1, "b": None}, ["Add", "a", "b"], 1.0),
        ({}, ["Greater", "a", 0.6], False),
        ({"a": None}, ["Greater", "a", 0.6], False),
        ({"color": "green"}, ["Switch", "undefined", 0, ["blue", 10]], 0),
        ({}, "a", "a"),
    ],
)
def test_unresolved_parameter_is_permissive_by_default(
    parameters, expression, expected_result
):
    assert create_solver(parameters)(expression) == expected_result


@pytest.mark.parametrize(
    "parameters, expression, construct, message",
    [
        ({"a": 3000}, ["Add", "a", "b"], "Add", "Parameter 'b' is not defined"),
        ({"a": 1, "b": None}, ["Add", "a", "b"], "Add", "Parameter 'b' is None"),
        ({}, ["Greater", "a", 0.6], "Greater", "Parameter 'a' is not defined"),
        ({"a": None}, ["Less", "a", 0.6], "Less", "Parameter 'a' is None"),
        ({"a": 2}, ["Multiply", "a", "b"], "Multiply", "Parameter 'b' is not defined"),
        (
            {"a": 0.7},
            ["All", ["Array", ["Greater", "a", 0.6], ["Less", "b", 1]]],
            "Less",
            "Parameter 'b' is not defined",
        ),
        ({}, "a", "Parameter", "Parameter 'a' is not defined"),
    ],
)
def test_unresolved_parameter_raises_in_strict_mode(
    parameters, expression, construct, message
):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver(parameters, strict=True)(expression)
    exception = exc_info.value
    assert isinstance(exception.e, MathJSONUnresolvedParameter)
    assert str(exception.e) == message
    assert exception.construct == construct


def test_unresolved_parameter_reports_innermost_expression():
    with pytest.raises(MathJSONException) as exc_info:
        create_solver({"a": 0.7}, strict=True)(
            ["Add", 1, ["Multiply", "a", "b"]]
        )
    assert exc_info.value.expr == ["Multiply", "a", "b"]


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({"a": 0.7}, ["Greater", "a", 0.6], True),
        ({"a": 0}, ["Add", "a", 1], 1.0),
        ({"a": False}, ["Not", "a"], True),
        ({"matrix": "plasma"}, ["Equal", "matrix", ["Str", "plasma"]], True),
        ({"plasma": 1}, ["Str", "plasma"], "plasma"),
        ({}, ["Constants", ["x", 5], ["Add", "x", 1]], 6.0),
        ({}, ["Constants", ["x", 0], ["Not", "x"]], True),
        ({}, ["Date", "2026-01-01"], datetime(2026, 1, 1)),
    ],
)
def test_strict_mode_resolved_expressions(parameters, expression, expected_result):
    assert create_solver(parameters, strict=True)(expression) == expected_result


@pytest.mark.parametrize(
    "parameters, expected_result",
    [({"a": 0.7}, True), ({"a": None}, True), ({}, False)],
)
def test_is_defined(parameters, expected_result):
    assert create_solver(parameters)(["IsDefined", "a"]) == expected_result
    assert (
        create_solver(parameters, strict=True)(["IsDefined", "a"])
        == expected_result
    )


@pytest.mark.parametrize(
    "expression, expected_result",
    [
        (["LogBase", 8, 2], 3.0),
        (["LogBase", 1000, 10], 3.0),
        (["LogBase", 100, 10], 2.0),
        (["LogBase", 0.001, 10], -3.0),
        (["LogBase", 81, 3], pytest.approx(4.0)),
        # Log is the natural logarithm, whatever the base
        (["Log", 100], math.log(100)),
        (["Log", 100, 10], math.log(100)),
        # The base of Log is not even evaluated
        (["Log", 100, "undefined"], math.log(100)),
        (["LogBase", 8, 0.5], pytest.approx(-3.0)),
        (["Log10", 1000], 3.0),
        (["Abs", -3.5], 3.5),
        (["Abs", 0], 0),
        (["Exp", 1], math.e),
        (["Ln", ["Exp", 1]], 1.0),
        (["Exp", 0], 1.0),
        (["Ln", ["Exp", 2]], 2.0),
        (["Root", -8, 3], -2.0),
        (["Root", -32, 5], -2.0),
        (["Root", -8, -3], -0.5),
        (["Root", -8, 3.0], -2.0),
        (["Power", 10, 2], 100),
        (["Power", 10, 0], 1),
        (["Power", 10, -3], 0.001),
        (["GreaterEqual", ["Log10", 1000], 3], True),
    ],
)
def test_calculator_operations(expression, expected_result):
    assert create_solver({}, strict=True)(expression) == expected_result


def test_integer_power_stays_an_integer():
    result = create_solver({}, strict=True)(["Power", 2, 3])
    assert result == 8 and isinstance(result, int)
    assert create_solver({}, strict=True)(["Square", 3]) == 9
    assert (
        create_solver({}, strict=True)(
            ["Switch", ["Power", 2, 3], ["Str", "other"], [8, ["Str", "eight"]]]
        )
        == "eight"
    )


@pytest.mark.parametrize(
    "parameters, expression",
    [
        ({}, ["Log10", 0]),
        ({}, ["Log10", -5]),
        ({}, ["Ln", 0]),
        ({}, ["Log", -1]),
        ({}, ["Log2", 0]),
        ({}, ["LogBase", 10, 1]),
        ({}, ["LogBase", 10, 0]),
        ({}, ["LogBase", 10, -2]),
        ({}, ["LogBase", 0, 10]),
        ({}, ["LogBase", -8, 2]),
        ({}, ["Sqrt", -4]),
        ({}, ["Root", -16, 4]),
        ({}, ["Root", -8, 2.5]),
        ({}, ["Power", -8, 0.5]),
        ({"u": -math.inf}, ["Sqrt", "u"]),
        ({"u": -math.inf}, ["Root", "u", 2]),
        ({"x": 0}, ["Divide", 1, ["Log10", "x"]]),
    ],
)
def test_domain_error(parameters, expression):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver(parameters, strict=True)(expression)
    assert isinstance(exc_info.value.e, MathJSONDomainError)


@pytest.mark.parametrize(
    "expression",
    [
        ["Power", 10, 400],
        ["Power", 10, 10**9],
        ["Power", 10.0, 400],
        ["Exp", 1000],
        ["Multiply", 1e300, 1e300],
        ["Add", 1e308, 1e308],
        ["Subtract", -1e308, 1e308],
        ["Divide", 1e308, 1e-10],
        ["Average", ["Array", 1e308, 1e308]],
        ["Median", ["Array", 1e308, 1e308]],
        ["Root", 10, 0.001],
        ["Less", ["Multiply", 1e300, 1e300], 1],
    ],
)
def test_overflow_error(expression):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver({}, strict=True)(expression)
    assert isinstance(exc_info.value.e, MathJSONOverflowError)


@pytest.mark.parametrize(
    "expression",
    [["Power", 10, -400], ["Power", 0.5, 2000], ["Exp", -1000]],
)
def test_underflow_error(expression):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver({}, strict=True)(expression)
    assert isinstance(exc_info.value.e, MathJSONUnderflowError)


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        # Crystal Miner gives an infinite relative uncertainty without positives
        ({"u": math.inf}, ["Less", ["Multiply", "u", 100], 50], False),
        ({"u": math.inf}, ["Multiply", "u", 100], math.inf),
        ({"u": math.inf}, ["Add", "u", 1], math.inf),
        ({"u": math.inf}, ["Divide", "u", 2], math.inf),
        ({"u": math.inf}, ["Power", "u", 2], math.inf),
        ({"u": -math.inf}, ["Exp", "u"], 0.0),
        ({"u": math.inf}, ["Power", "u", -1], 0.0),
        ({"u": 0}, ["Power", "u", 2], 0),
        ({"u": "inf"}, ["Multiply", "u", 2], math.inf),
        ({"u": -math.inf}, ["Root", "u", 3], -math.inf),
        ({"u": 2}, ["LogBase", 8, ["Multiply", "u", math.inf]], 0.0),
        # An integer too large for a float stays an exact integer
        ({}, ["Subtract", 10**400, 1], 10**400 - 1),
    ],
)
def test_non_finite_data_go_through(parameters, expression, expected_result):
    assert create_solver(parameters, strict=True)(expression) == expected_result


def test_nan_data_go_through():
    result = create_solver({"u": math.nan}, strict=True)(["Multiply", "u", 2])
    assert math.isnan(result)


@pytest.mark.parametrize("expression", [["Floor", 2.5], ["Sin", "x"]])
def test_unsupported_operator_raises_in_strict_mode(expression):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver({"x": 1}, strict=True)(expression)
    assert isinstance(exc_info.value.e, MathJSONUnsupportedOperator)
    # The default mode still returns it unchanged
    assert create_solver({"x": 1})(expression) == expression


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({"l": ["Array", "plasma", "serum"]}, ["In", ["Str", "plasma"], "l"], True),
        ({"l": ["plasma", "serum"]}, ["In", ["Str", "plasma"], "l"], True),
        ({"l": ["A1", "B2"]}, "l", ["A1", "B2"]),
        (
            {"rows": ["Array", ["plasma", 1]]},
            ["Map", "rows", ["Str"]],
            ["Array", "['plasma', 1]"],
        ),
        (
            {"rows": ["plasma", "serum"]},
            ["Constants", ["l", "rows"], ["In", ["Str", "plasma"], "l"]],
            True,
        ),
        (
            {"rows": ["Array", ["plasma", 1]]},
            ["Constants", ["r", "rows"], ["Map", "r", ["Str"]]],
            ["Array", "['plasma', 1]"],
        ),
        (
            {"rows": ["Array", ["plasma", 1]]},
            ["Constants", ["r", "rows"], ["Map", "r", ["Abs"]]],
            ["Array", ["plasma", 1]],
        ),
    ],
)
def test_list_parameters_are_data_in_strict_mode(
    parameters, expression, expected_result
):
    assert create_solver(parameters, strict=True)(expression) == expected_result


@pytest.mark.parametrize(
    "parameters, expression, error",
    [
        (
            {"x": 0},
            ["If", [["Greater", ["Log10", "x"], 1], 1], 2],
            MathJSONDomainError,
        ),
        ({"x": 0}, ["If", [True, ["Log10", "x"]], 2], MathJSONDomainError),
        ({}, ["If", [True, ["Power", 10, 400]], 2], MathJSONOverflowError),
        ({}, ["If", [["Floor", 1], 1], 2], MathJSONUnsupportedOperator),
        ({}, ["Map", ["Array", 1, 0], ["Log10"]], MathJSONDomainError),
        ({}, ["Map", ["Array", 1, -1000], ["Exp"]], MathJSONUnderflowError),
        ({}, ["Map", ["Array", 1, 1000], ["Exp"]], MathJSONOverflowError),
        ({}, ["Map", ["Array", 1], ["Floor"]], MathJSONUnsupportedOperator),
        ({}, ["If", [True, ["Exp", -1000]], 2], MathJSONUnderflowError),
    ],
)
def test_if_and_map_let_calculation_errors_through(
    parameters, expression, error
):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver(parameters, strict=True)(expression)
    assert isinstance(exc_info.value.e, error)


@pytest.mark.parametrize(
    "parameters, expression",
    [
        ({"x": 0}, ["If", [["Greater", ["Log10", "x"], 1], 1], 2]),
        ({}, ["Map", ["Array", 1, 0], ["Log10"]]),
    ],
)
def test_if_and_map_let_calculation_errors_through_by_default(
    parameters, expression
):
    with pytest.raises(MathJSONException) as exc_info:
        create_solver(parameters)(expression)
    assert isinstance(exc_info.value.e, MathJSONDomainError)


@pytest.mark.parametrize(
    "parameters, expression, expected_result",
    [
        ({}, ["If", [["Greater", "missing", 1], 1], 2], 2),
        ({}, ["If", [True, ["Root", 8, 0]], 2], 2),
        ({}, ["Map", ["Array", 1, 2], ["Divide", 0]], ["Array", 1, 2]),
    ],
)
def test_if_and_map_still_catch_other_errors(
    parameters, expression, expected_result
):
    assert create_solver(parameters, strict=True)(expression) == expected_result


def test_extract_variables_knows_log_base():
    assert extract_variables(["LogBase", "x", 2], set(), set()) == {"x"}


def test_list_in_the_given_context_is_data_in_strict_mode():
    assert (
        create_solver({}, strict=True)(
            ["In", ["Str", "plasma"], "l"], {"l": ["plasma", "serum"]}
        )
        is True
    )


def test_nested_list_in_the_given_context_is_data_in_strict_mode():
    solver = create_solver({}, strict=True)
    context = {"r": ["Array", ["plasma", 1]]}
    assert solver(["Map", "r", ["Str"]], context) == ["Array", "['plasma', 1]"]
    # The context's lists are data for that call only
    with pytest.raises(MathJSONException) as exc_info:
        solver(["Constants", ["x", context["r"][1]], "x"])
    assert isinstance(exc_info.value.e, MathJSONUnsupportedOperator)
