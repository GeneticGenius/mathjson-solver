# Changelog

Git tags of this fork (`1.10.0-N`) do not follow the package version declared in `setup.py`.

| Tag | Package version | Changes |
|---|---|---|
| `1.10.0-5` | `1.14.0.post5` | `LogBase` operator. Out-of-domain, overflow and underflow errors; strict mode rejects unsupported operators; `If` and `Map` let these errors through. Details below. |
| `1.10.0-4` | `1.14.0` | `create_solver(parameters, strict=True)`: an undefined or `None` parameter raises a `MathJSONException` caused by `MathJSONUnresolvedParameter`. `IsDefined` implemented. `Str` and `Not` keep the `Constants` context. `extract_variables` reads the final expression of `Constants` and ignores `Str` / `Date` literals. |
| `1.10.0-3` | `1.14.0` | `Date` operator. |
| `1.10.0-2` | `1.14.0` | Comparison operators accept multiple operands. |
| `1.10.0-1` | `1.10.0` | `Rational` and `Ln` operators. |

## 1.10.0-5 (package version 1.14.0.post5)

### Added
- `["LogBase", x, b]`: logarithm of `x` in base `b`, exact for bases 10 and 2 (`["LogBase", 1000, 10]` is `3.0`, `["LogBase", 8, 2]` is `3.0`).
- Exceptions exported from `mathjson_solver`, found as the `e` of the `MathJSONException`:
  - `MathJSONDomainError` (a `ValueError`): logarithm (`Ln`, `Log`, `Log2`, `Log10`, `LogBase`) of a number `<= 0`, base `<= 0` or `== 1`, root (`Sqrt`, `Root`) of a negative number whose exponent `1/n` is not an integer, e.g. `["Root", -16, 4]`, power of a negative number with a non-integer exponent. No result is a complex number any more.
  - `MathJSONOverflowError` (an `OverflowError`): a calculation on finite numbers whose result is infinite, NaN or too large for a float, e.g. `["Power", 10, 400]`, `["Exp", 1000]`, `["Multiply", 1e300, 1e300]`. Any other `OverflowError` raised by an operator is converted to it.
  - `MathJSONUnderflowError` (an `ArithmeticError`): `Power` or `Exp` of finite numbers whose non-zero result becomes `0.0`, e.g. `["Power", 10, -400]`, `["Exp", -1000]`.
  - `MathJSONUnsupportedOperator` (a `NotImplementedError`): in strict mode, a formula whose operator is unknown, e.g. `["Floor", 2.5]`. A list given as a parameter value, at any depth, is data and is still returned as is.
- `Root` of a negative number with an odd index is real: `["Root", -8, 3]` is `-2.0`.

### Changed
- Infinite and NaN values coming from the parameters raise neither an overflow nor an underflow: only finite operands do. Converting an infinite value to an integer (`Round`, `Int`) still fails, now as a `MathJSONOverflowError`.
- `If` and `Map` let the errors above through instead of falling back to the `else` branch or to the element. Any other `MathJSONException` is still caught. For instance, `["If", [["Greater", ["Log10", "x"], 1], 1], 2]` with `x = 0` gave `2` and now raises a domain error.

### Unchanged
- `["Log", x]` is still the natural logarithm, whatever its base argument.
- `Power` of integers still gives an integer: `["Power", 2, 3]` is `8`.
