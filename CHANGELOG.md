# Changelog

## 1.10.0-4 (package version 1.14.0.post4)

The Git tags of this fork (`1.10.0-x`) and the package version differ: tags `1.10.0-2` and `1.10.0-3` already declare version `1.14.0`, because upstream 1.14.0 was merged between `1.10.0-1` and `1.10.0-2`. Tag `1.10.0-4` declares `1.14.0.post4`, so the installed version keeps increasing (`pip show mathjson-solver`).

| Git tag | Package version |
|---|---|
| 1.10.0-1 | 1.10.0 |
| 1.10.0-2 | 1.14.0 |
| 1.10.0-3 | 1.14.0 |
| 1.10.0-4 | 1.14.0.post4 |

### Breaking changes
- **`["Log", x]` is now the base-10 logarithm** (it was the natural logarithm). This aligns the solver with the CortexJS Compute Engine used by the front end. Consumers must migrate stored `["Log", x]` expressions to `["Ln", x]` to keep the previous behaviour.
- **Python >= 3.11 is required** (`math.cbrt`).
- Out-of-domain and non-finite results now raise instead of returning a value (see below).

### Added
- `["Log", x, b]`: logarithm of `x` in base `b`.
- `MathJSONDomainError` (subclass of `ValueError`, exported from `mathjson_solver`). It is the inner exception (`MathJSONException.e`) when arguments are outside the mathematical domain of an operator:
  - `Log`, `Ln`, `Log2`, `Log10` with `x <= 0`; `Log` with base `<= 0` or base `== 1`.
  - `Sqrt` of a negative number.
  - `Power` with a negative base and a non-integer exponent. (`Power(0, negative)` still raises `ZeroDivisionError`.)
  - `Root` of a negative number with an even or fractional index.
- `Root` supports odd roots of negative numbers: `["Root", -8, 3]` is `-2` and `["Root", -32, 5]` is `-2`. `∛` uses `math.cbrt`, so `["Root", 27, 3]` is exactly `3.0`.
- Overflow handling: `OverflowError` is converted to `MathJSONException`. A float result that is infinite raises `OverflowError`, and a NaN result raises `MathJSONDomainError`, e.g. `["Multiply", 1e300, 1e300]`, `["Power", 10, 400]`. The check applies to float results of any construct only; booleans, strings, lists and dates are unaffected.
- `ExponentialE` evaluates to `math.e`. Parameters and `Constants` with the same name take precedence. `Pi` is intentionally not provided.
- `create_solver(parameters, strict=False)`. With `strict=True`, an expression whose head is not a supported operator raises `MathJSONException` (caused by `NotImplementedError`) instead of being returned unchanged. The default behaviour is unchanged.
- `extract_variables` knows `Ln` and `Rational`, and does not report `ExponentialE` as a variable.

### Changed
- `Power`, `Sqrt`, `Root` and `Square` use `math.pow` (never produce complex numbers) and return floats, e.g. `["Power", 2, 3]` is `8.0` (equal to `8`).

### Packaging / CI
- `setup.cfg` and `setup.py` version set to `1.14.0.post4` (tag `1.10.0-4`).
- GitHub workflows test on Python 3.11 and 3.14 with `actions/setup-python@v5`.
