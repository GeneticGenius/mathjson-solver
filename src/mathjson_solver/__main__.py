import numbers
from typing import Union
from functools import reduce
from datetime import datetime, date, timedelta
import logging
import math
import operator
import traceback
from copy import deepcopy
from statistics import median

NoneType = type(None)


class MathJSONException(Exception):
    """Exception for MathJSON processing issues"""

    def __init__(self, e, expr, *args, **kwargs):
        super().__init__(args)
        self.e = e
        self.expr = expr
        self.construct = kwargs.get("mathjson_construct", "MathJSON")

    def __str__(self):
        if hasattr(self.e, "message"):
            m = self.e.message
        else:
            m = str(self.e)
        return f"Problem in {self.construct}. {self.expr}. {m}"


class MathJSONUnresolvedParameter(KeyError):
    """A parameter is not defined, or is None, in strict mode"""

    def __str__(self):
        return str(self.args[0])


class MathJSONDomainError(ValueError):
    """The arguments are outside the mathematical domain of the operator"""


class MathJSONOverflowError(OverflowError):
    """A calculation on finite numbers gives a result too large for a float"""


class MathJSONUnderflowError(ArithmeticError):
    """A calculation gives a non-zero result too small for a float, so 0"""


class MathJSONUnsupportedOperator(NotImplementedError):
    """The formula uses an operator the solver does not know"""


# Errors of an impossible calculation: `If` and `Map` let them through
CALCULATION_ERRORS = (
    MathJSONDomainError,
    MathJSONOverflowError,
    MathJSONUnderflowError,
    MathJSONUnsupportedOperator,
)

LARGEST_FLOAT = 1.7976931348623157e308
# Above this many digits, an integer power is too large for a float: refuse
# it without computing it, which could take forever (10 ** 10 ** 9)
MAX_POWER_DIGITS = 400


def is_calculation_error(exception):
    return isinstance(exception.e, CALCULATION_ERRORS)


def is_non_finite(x):
    """Whether `x` is an infinite or NaN number, or such a number as a string"""
    if isinstance(x, bool):
        return False
    try:
        if isinstance(x, str):
            x = float(x)
        return isinstance(x, numbers.Number) and not math.isfinite(x)
    except (TypeError, ValueError, OverflowError):
        # OverflowError: an integer too large for a float, still finite
        return False


def has_fraction(x):
    """Whether `x` is a finite number that is not an integer"""
    if isinstance(x, str):
        return False
    try:
        x = float(x)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(x) and not x.is_integer()


def is_negative(x):
    try:
        return x < 0
    except TypeError:
        return False


def finite(result, *operands):
    """`result`, unless finite operands gave an infinite or NaN result"""
    if is_non_finite(result) and not any(is_non_finite(x) for x in operands):
        raise MathJSONOverflowError("Result is not a finite number")
    return result


def not_underflowed(result, *operands):
    """`result`, unless finite operands gave 0 instead of a tiny number"""
    if (
        result == 0
        and isinstance(result, float)
        and not any(is_non_finite(x) for x in operands)
    ):
        raise MathJSONUnderflowError("Result is too small to be represented")
    return result


def in_domain(fn, *args):
    """`fn(*args)`, a math domain error being a MathJSONDomainError"""
    try:
        return fn(*args)
    except ValueError as e:
        raise MathJSONDomainError(str(e)) from e


def power(x, y):
    """`x ** y` as Python computes it, without complex nor non-finite result"""
    if (
        isinstance(x, int)
        and isinstance(y, int)
        and abs(x) > 1
        and y * math.log10(abs(x)) > MAX_POWER_DIGITS
    ):
        raise MathJSONOverflowError("Result is too large for a float")
    if is_negative(x) and has_fraction(y):
        raise MathJSONDomainError(
            "Power of a negative number with a non-integer exponent"
        )
    result = pow(x, y)
    if isinstance(result, int) and abs(result) > LARGEST_FLOAT:
        raise MathJSONOverflowError("Result is too large for a float")
    if x != 0:
        not_underflowed(result, x, y)
    return finite(result, x, y)


def root(x, n):
    """The `n`-th root of `x`: real for an odd root of a negative number"""
    exponent = 1.0 / n
    is_odd = float(n).is_integer() and int(n) % 2 == 1
    if x < 0 and is_odd:
        return -power(-x, exponent)
    return power(x, exponent)


def log_base(x, base):
    if base <= 0 or base == 1:
        raise MathJSONDomainError(
            "Logarithm base must be positive and not equal to 1"
        )
    if base == 10:
        return in_domain(math.log10, x)
    if base == 2:
        return in_domain(math.log2, x)
    return in_domain(math.log, x, base)


def exp(x):
    return not_underflowed(math.exp(x), x)


def is_numeric(x):
    try:
        float(x)
    except ValueError:
        return False
    except TypeError:
        return False
    else:
        return True


def has_matching_sublist(
    *,
    my_list: list,
    required_match_count: int,
    position: int,
    contiguous: bool,
    conditions: list[bool],
) -> bool:
    if contiguous:
        # Check for contiguous matches based on position
        if position == 0:
            # Check if the beginning of the list matches
            count = sum(
                1
                for i in range(min(required_match_count, len(my_list)))
                if conditions[i]
            )
            return count == required_match_count
        elif position > 0:
            # Skip the first `position` elements
            count = sum(
                1
                for i in range(position, position + required_match_count)
                if i < len(my_list) and conditions[i]
            )
            return count == required_match_count
        elif position == -1:
            # Check if the end of the list matches
            count = sum(
                1
                for i in range(
                    len(my_list) - required_match_count, len(my_list)
                )
                if conditions[i]
            )
            return count == required_match_count
        elif position < -1:
            # Skip the last `abs(position)` elements
            count = sum(
                1 for i in range(len(my_list) + position) if conditions[i]
            )
            return count == required_match_count
    else:
        # Check for non-contiguous matches
        count = sum(1 for i in range(len(my_list)) if conditions[i])
        return count >= required_match_count


def comparison_safe_converter(x):
    if type(x) in [int, float, str]:
        return f"{x}"
    elif type(x) in [bool, NoneType]:
        if x:
            return True
        else:
            return False
    return x


def comparison_safe_converter_for_pairs(
    v1, v2
) -> (Union[str, float], Union[str, float]):
    if is_numeric(v1):
        v1 = float(v1)
    if is_numeric(v2):
        v2 = float(v2)
    return v1, v2


def has_sublist2(
    *,
    my_list: list,
    required_match_count: int,
    position: int,
    contiguous: bool,
    condition: callable,
) -> bool:
    if contiguous:
        # Check for contiguous matches based on position
        if position == 0:
            # Check if the beginning of the list matches
            count = sum(
                1 for x in my_list[:required_match_count] if condition(x)
            )
            return count == required_match_count
        elif position > 0:
            # Skip the first `position` elements
            count = sum(
                1
                for x in my_list[position : position + required_match_count]
                if condition(x)
            )
            return count == required_match_count
        elif position == -1:
            # Check if the end of the list matches
            count = sum(
                1 for x in my_list[-required_match_count:] if condition(x)
            )
            return count == required_match_count
        elif position < -1:
            # Skip the last `abs(position)` elements
            count = sum(1 for x in my_list[:position] if condition(x))
            return count == required_match_count
    else:
        # Check for non-contiguous matches
        count = sum(1 for x in my_list if condition(x))
        return count >= required_match_count


def create_mathjson_solver(solver_parameters, strict=False):
    def resolved(name, value):
        if strict and value is None:
            raise MathJSONUnresolvedParameter(f"Parameter '{name}' is None")
        return value

    def list_ids(value, ids):
        if isinstance(value, list):
            ids[id(value)] = value
            for x in value:
                list_ids(x, ids)
        return ids

    # Lists given as parameter values, at any depth, are data, not formulas.
    # Copies of the context keep them as they are, so they stay recognized.
    data_lists = {}
    for value in solver_parameters.values():
        list_ids(value, data_lists)

    def resolve_value(value, c):
        if strict and isinstance(value, str):
            return value
        return f(value, c)

    def f(s, *args):
        if args:
            c = deepcopy(args[0], dict(data_lists))
        else:
            c = {}
        #         c = deepcopy(kwargs.get("c", {}))
        if isinstance(s, numbers.Number):
            return s
        if isinstance(s, list):

            def Arr(s):
                return s

            def Add(s):
                l_res = []
                tmp = 0
                for i, x in enumerate(s[1:]):
                    res = f(x, c)
                    if is_numeric(res):
                        res = float(res)
                    l_res.append(res)
                    if i == 0:
                        tmp = res
                    else:
                        try:
                            tmp = tmp + res
                        except TypeError:
                            pass

                    # if isinstance(res, list):
                    #     l_res.append(sum([xx for xx in res[1:]]))
                    # else:
                    #     l_res.append(res)

                return finite(tmp, *l_res)

                # tmp = 0
                # for i, x in enumerate(l):
                #     if i == 0:
                #         tmp = x
                #     else:
                #         tmp = tmp + x
                # return tmp

            # def Sum(s):
            #     l_res = []
            #     for x in s[1:]:
            #         res = f(x, c)
            #         if isinstance(res, list):
            #             l_res.append(sum([xx for xx in res[1:]]))
            #         else:
            #             l_res.append(res)
            #     return sum(l_res)

            def Sum(s):
                l_res = ["Array"]
                for x in s[1:]:
                    res = f(x, c)
                    if isinstance(res, list):
                        l_res.append(Add(["Array"] + [xx for xx in res[1:]]))
                    else:
                        l_res.append(res)
                return Add(l_res)

            def Max(s):
                if isinstance(s[1], str):
                    return max(
                        [f(x, c) for x in f(s[1], c) if is_numeric(f(x, c))]
                    )
                else:
                    return max(
                        [f(x, c) for x in s[1][1:] if is_numeric(f(x, c))]
                    )

            def Min(s):
                if isinstance(s[1], str):
                    return min(
                        [f(x, c) for x in f(s[1], c) if is_numeric(f(x, c))]
                    )
                else:
                    return min(
                        [f(x, c) for x in s[1][1:] if is_numeric(f(x, c))]
                    )

            def Average(s):
                if isinstance(s[1], str):
                    # A reference to "answer" has been passed
                    s_ = [
                        float(f(x, c))
                        for x in f(s[1], c)
                        if is_numeric(f(x, c))
                    ]
                else:
                    s_ = [
                        float(f(x, c)) for x in s[1][1:] if is_numeric(f(x, c))
                    ]
                # print(f"{s_} {sum(s_)}/{len(s_)}")
                try:
                    return finite(sum(s_) / len(s_), *s_)
                except ZeroDivisionError:
                    return None

            def Median(s):
                if isinstance(s[1], str):
                    values = [f(x, c) for x in f(s[1], c) if is_numeric(f(x, c))]
                else:
                    values = [f(x, c) for x in s[1][1:] if is_numeric(f(x, c))]
                return finite(median(values), *values)

            def Length(s):
                if isinstance(s[1], str):
                    return len([x for x in f(s[1], c)][1:])
                else:
                    return len([x for x in s[1][1:]])

            def Any(s):
                return any([f(x, c) for x in s[1][1:]])

            def All(s):
                return all([f(x, c) for x in s[1][1:]])

            def Int(s):
                try:
                    return int(f(s[1], c))
                except ValueError:
                    return int(float(f(s[1], c)))

            def Float(s):
                return float(f(s[1], c))

            def Constants(s):
                for x in s[1:-1]:
                    c[x[0]] = f(x[1], c)
                return f(s[-1], c)

            def Switch(s):
                expression = f(s[1], c)
                for x in s[3:]:
                    if len(x) != 2:
                        raise ValueError(
                            "Case of 'Switch' should have exactly two parameters"
                        )
                    if comparison_safe_converter(
                        expression
                    ) == comparison_safe_converter(f(x[0], c)):
                        return f(x[1], c)
                else:
                    return f(s[2], c)

            def StrictSwitch(s):
                expression = f(s[1], c)
                for x in s[3:]:
                    if len(x) != 2:
                        raise ValueError(
                            "Case of 'StrictSwitch' should have exactly two parameters"
                        )
                    if expression == f(x[0], c):
                        return f(x[1], c)
                else:
                    return f(s[2], c)

            def If(s):
                if len(s) < 3:
                    raise ValueError("Wrong parameters for 'If'")
                for x in s[1:-1]:
                    if len(x) != 2:
                        raise ValueError("Wrong if or elif in 'If'")
                    try:
                        if f(x[0], c):
                            try:
                                return f(x[1], c)
                            except MathJSONException as e:
                                if is_calculation_error(e):
                                    raise
                                logging.error(
                                    "MathJSONException: %s",
                                    traceback.format_exc(),
                                )
                                continue
                    except MathJSONException as e:
                        if is_calculation_error(e):
                            raise
                        logging.error(
                            "MathJSONException: %s", traceback.format_exc()
                        )
                        return f(s[-1], c)  # return default value (else)

                return f(s[-1], c)

            def In(s):
                if len(s) != 3:
                    raise ValueError("Wrong parameters for 'In'")
                if isinstance(s[2], list) and s[2][0] == "Array":
                    return f(s[1], c) in [f(x, c) for x in s[2][1:]]

                elif isinstance(s[2], str):
                    return f(s[1], c) in f(s[2], c)
                else:
                    raise ValueError(
                        "Wrong parameters for 'In'. Parameter 2 must be a list."
                    )

            def Not_in(s):
                return not In(s)

            def Contains_any_of(s):
                if isinstance(s[1], list) and s[1][0] == "Array":
                    list1 = [f(x, c) for x in s[1][1:]]
                elif isinstance(s[1], str):
                    list1 = f(s[1], c)

                if isinstance(s[2], list) and s[2][0] == "Array":
                    list2 = [f(x, c) for x in s[2][1:]]
                elif isinstance(s[2], str):
                    list2 = f(s[2], c)

                if any(x in list1 for x in list2):
                    return True
                return False

            def Contains_all_of(s):
                if isinstance(s[1], list) and s[1][0] == "Array":
                    list1 = [f(x, c) for x in s[1][1:]]
                elif isinstance(s[1], str):
                    list1 = f(s[1], c)

                if isinstance(s[2], list) and s[2][0] == "Array":
                    list2 = [f(x, c) for x in s[2][1:]]
                elif isinstance(s[2], str):
                    list2 = f(s[2], c)

                if all(x in list1 for x in list2):
                    return True
                return False

            def Contains_none_of(s):
                return not Contains_any_of(s)

            def Str(s):
                if len(s) < 2:
                    raise ValueError("Wrong parameters for 'Str'")
                if strict and isinstance(s[1], str):
                    return s[1]
                return f"{f(s[1], c)}"

            def Date(s):
                if len(s) < 2:
                    raise ValueError("Wrong parameters for 'Date'")
                return datetime.fromisoformat(s[1])

            def Not(s):
                return not f(s[1], c)

            def IsDefined(s):
                return s[1] in solver_parameters or s[1] in c

            def Map(s):
                """
                ["Map", list, function, more parameters]
                The `function` must accept at least one parameter. That is for the current loop element.
                The `more parameters` are for any additional parameters that function might have.
                """
                z = f(s[1], c)
                if isinstance(z, list):
                    retlist = ["Array"]
                    for x in z[1:]:
                        try:
                            the_function_name = s[2][0]
                            ss = [the_function_name, x] + s[3:]
                            retlist.append(f(ss, c))
                        except MathJSONException as e:
                            if is_calculation_error(e):
                                raise
                            retlist.append(x)
                    return retlist

            def StrictMap(s):
                """
                ["Map", list, function, more parameters]
                The `function` must accept at least one parameter. That is for the current loop element.
                The `more parameters` are for any additional parameters that function might have.
                """
                z = f(s[1], c)
                if isinstance(z, list):
                    retlist = ["Array"]
                    for x in z[1:]:
                        the_function_name = s[2][0]
                        ss = [the_function_name, x] + s[3:]
                        retlist.append(f(ss, c))
                    return retlist

            def Filter(s):
                """
                ["Filter", list, function, more parameters]
                The `function` must accept at least one parameter. That is for the current loop element.
                The `more parameters` are for any additional parameters that function might have.
                """
                z = f(s[1], c)
                if isinstance(z, list):
                    retlist = ["Array"]
                    for x in z[1:]:
                        the_function_name = s[2][0]
                        ss = [the_function_name, x] + s[3:]
                        if f(ss, c):
                            retlist.append(x)
                    return retlist

            def HasMatchingSublist(s):
                """
                ["HasMatchingSublist", list, required_match_count, position, contiguous, function, more parameters]
                """
                the_list = f(s[1], c)[1:]
                required_match_count = f(s[2], c)
                position = f(s[3], c)
                contiguous = f(s[4], c)
                conditions = []

                for i, x in enumerate(the_list):
                    the_function_name = s[5][0]
                    ss = [the_function_name, x] + s[6:]
                    conditions.append(f(ss, c))
                    pass

                return has_matching_sublist(
                    my_list=the_list,
                    required_match_count=required_match_count,
                    position=position,
                    contiguous=contiguous,
                    conditions=conditions,
                )

            def Strptime(s):
                datetime_str = f(s[1], c)
                parameters = f(s[2], c)
                return datetime.strptime(datetime_str, parameters)

            def Strftime(s):
                dt = f(s[1], c)
                parameters = f(s[2], c)
                return dt.strftime(parameters)

            def Now(s):
                return datetime.now()

            def Today(s):
                return date.today()

            def TimeDeltaDays(s):
                return timedelta(days=f(s[1], c))

            def TimeDeltaMinutes(s):
                return timedelta(minutes=f(s[1], c))

            def TimeDeltaHours(s):
                return timedelta(hours=f(s[1], c))

            def TimeDeltaWeeks(s):
                return timedelta(weeks=f(s[1], c))

            def Compare(op, s, c):
                """
                Compare multiple operands using the given binary operator,
                after coercing each operand to float.

                Args:
                    op: A binary function like operator.lt, operator.gt, operator.eq.
                    s: A MathJSON-style list, e.g. ["Less", "a", "b", "c"].
                    c: A context passed down to f().

                Returns:
                    bool: True if the chain of comparisons holds, False otherwise.
                """

                def safe_float(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return val

                values = [safe_float(f(s[i], c)) for i in range(1, len(s))]
                try:
                    return all(
                        op(values[i], values[i + 1])
                        for i in range(len(values) - 1)
                    )
                except TypeError:
                    return False

            def reduced(operation, s):
                values = [f(x, c) for x in s[1:]]
                return finite(reduce(operation, values), *values)

            def Divide(s):
                x = f(s[1], c)
                y = f(s[2], c)
                return finite(x / y, x, y)

            constructs = {
                "Sum": Sum,
                "Add": Add,
                "Subtract": lambda s: reduced(lambda a, b: a - b, s),
                "Constants": Constants,
                "Switch": Switch,
                "StrictSwitch": StrictSwitch,
                "If": If,
                "Multiply": lambda s: reduced(
                    lambda a, b: float(a) * float(b), s
                ),
                "Divide": Divide,
                "Rational": Divide,
                "Negate": lambda s: -f(s[1], c),
                "Power": lambda s: power(f(s[1], c), f(s[2], c)),
                "Root": lambda s: root(f(s[1], c), f(s[2], c)),
                "Sqrt": lambda s: power(f(s[1], c), 1.0 / 2),
                "Square": lambda s: power(f(s[1], c), 2),
                "Exp": lambda s: exp(f(s[1], c)),
                # Log is the natural logarithm, whatever the base
                "Log": lambda s: in_domain(math.log, f(s[1], c)),
                "Ln": lambda s: in_domain(math.log, f(s[1], c)),
                "Log2": lambda s: in_domain(math.log2, f(s[1], c)),
                "Log10": lambda s: in_domain(math.log10, f(s[1], c)),
                "LogBase": lambda s: log_base(f(s[1], c), f(s[2], c)),
                "Less": lambda s: Compare(operator.lt, s, c),
                "Greater": lambda s: Compare(operator.gt, s, c),
                "Equal": lambda s: Compare(operator.eq, s, c),
                "LessEqual": lambda s: Compare(operator.le, s, c),
                "GreaterEqual": lambda s: Compare(operator.ge, s, c),
                "NotEqual": lambda s: Compare(operator.ne, s, c),
                "Abs": lambda s: abs(f(s[1], c)),
                "Round": lambda s: (
                    round(f(s[1], c), f(s[2], c))
                    if len(s) == 3
                    else int(round(f(s[1], c)))
                ),
                "Max": Max,
                "Min": Min,
                "Average": Average,
                "Median": Median,
                "Length": Length,
                "Any": Any,
                "All": All,
                "Array": Arr,
                "In": In,
                "Not_in": Not_in,
                "Contains_any_of": Contains_any_of,
                "Contains_all_of": Contains_all_of,
                "Contains_none_of": Contains_none_of,
                "NotIn": Not_in,
                "ContainsAnyOf": Contains_any_of,
                "ContainsAllOf": Contains_all_of,
                "ContainsNoneOf": Contains_none_of,
                "Int": Int,
                "Float": Float,
                "Str": Str,
                "Date": Date,
                "Not": Not,
                "IsDefined": IsDefined,
                "Map": Map,
                "StrictMap": StrictMap,
                "Filter": Filter,
                "HasMatchingSublist": HasMatchingSublist,
                "Strptime": Strptime,
                "Strftime": Strftime,
                "Today": Today,
                "Now": Now,
                "TimeDeltaWeeks": TimeDeltaWeeks,
                "TimeDeltaHours": TimeDeltaHours,
                "TimeDeltaMinutes": TimeDeltaMinutes,
                "TimeDeltaDays": TimeDeltaDays,
            }
            if s[0] in constructs:
                try:
                    return constructs[s[0]](s)

                # except RecursionError:
                #     return s[0]
                # except Exception as e:
                except TypeError as e:
                    raise MathJSONException(e, s, mathjson_construct=s[0])
                except ValueError as e:
                    raise MathJSONException(e, s, mathjson_construct=s[0])
                except IndexError as e:
                    raise MathJSONException(e, s, mathjson_construct=s[0])
                except ZeroDivisionError as e:
                    raise MathJSONException(e, s, mathjson_construct=s[0])
                except OverflowError as e:
                    if not isinstance(e, MathJSONOverflowError):
                        e = MathJSONOverflowError(str(e))
                    raise MathJSONException(e, s, mathjson_construct=s[0])
                except MathJSONUnderflowError as e:
                    raise MathJSONException(e, s, mathjson_construct=s[0])
                except MathJSONUnresolvedParameter as e:
                    raise MathJSONException(e, s, mathjson_construct=s[0])
            else:
                if (
                    strict
                    and isinstance(s[0], str)
                    and id(s) not in data_lists
                ):
                    raise MathJSONException(
                        MathJSONUnsupportedOperator(f"'{s[0]}' is not supported"),
                        s,
                        mathjson_construct=s[0],
                    )
                return s
        elif s in solver_parameters:
            value = resolved(s, solver_parameters[s])
            try:
                return resolve_value(value, c)
            except RecursionError:
                return value
        elif s in c:
            return resolve_value(resolved(s, c[s]), c)
        else:
            if strict and isinstance(s, str):
                raise MathJSONUnresolvedParameter(f"Parameter '{s}' is not defined")
            return s

    def solver(s, *args):
        # The lists of a given context are data too, during this call only
        context_lists = {}
        if args and isinstance(args[0], dict):
            for value in args[0].values():
                list_ids(value, context_lists)
        added = context_lists.keys() - data_lists.keys()
        data_lists.update((k, context_lists[k]) for k in added)
        try:
            return f(s, *args)
        except MathJSONUnresolvedParameter as e:
            raise MathJSONException(e, s, mathjson_construct="Parameter")
        finally:
            for k in added:
                del data_lists[k]

    return solver


def extract_variables(
    s: Union[list, int, float, str], li: set, ignore_list: set
):
    constructs = [
        "Add",
        "Sum",
        "Subtract",
        "Constants",
        "Switch",
        "If",
        "Multiply",
        "Divide",
        "Negate",
        "Power",
        "Root",
        "Sqrt",
        "Square",
        "Exp",
        "Log",
        "Log2",
        "Log10",
        "LogBase",
        "Equal",
        "Greater",
        "GreaterEqual",
        "Less",
        "LessEqual",
        "NotEqual",
        "Abs",
        "Round",
        "Max",
        "Min",
        "Average",
        "Median",
        "Length",
        "Any",
        "All",
        "Array",
        "In",
        "Not_in",
        "Contains_any_of",
        "Contains_all_of",
        "Contains_none_of",
        "NotIn",
        "ContainsAnyOf",
        "ContainsAllOf",
        "ContainsNoneOf",
        "Int",
        "Float",
        "Str",
        "Not",
        "IsDefined",
        "Map",
        "HasMatchingSublist",
        "Strptime",
        "Strftime",
        "Today",
        "Now",
        "TimeDeltaWeeks",
        "TimeDeltaHours",
        "TimeDeltaMinutes",
        "TimeDeltaDays",
    ]
    if isinstance(s, str):
        if s in ignore_list:
            return li
        if s not in constructs:
            li.add(s)
        return li
    elif isinstance(s, list):
        if s[0] == "Constants":
            for x in s[1:-1]:
                ignore_list.add(x[0])
                li.update(extract_variables(x[1], li, ignore_list))
            li.update(extract_variables(s[-1], li, ignore_list))
        elif s[0] in ("Str", "Date"):
            return li
        elif s[0] == "If":
            for elif_block in s[1:-1]:  # s[1] is list
                for x in elif_block:
                    li.update(extract_variables(x, li, ignore_list))
            li.update(extract_variables(s[-1], li, ignore_list))
        else:
            for x in s[1:]:
                li.update(extract_variables(x, li, ignore_list))
        return li
    else:
        return li
