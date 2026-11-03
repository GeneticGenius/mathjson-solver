# Changelog

Git tags of this fork (`1.10.0-N`) do not follow the package version declared in `setup.py`.

| Tag | Package version | Changes |
|---|---|---|
| `1.10.0-4` | `1.14.0` | `create_solver(parameters, strict=True)`: an undefined or `None` parameter raises a `MathJSONException` caused by `MathJSONUnresolvedParameter`. `IsDefined` implemented. `Str` and `Not` keep the `Constants` context. `extract_variables` reads the final expression of `Constants` and ignores `Str` / `Date` literals. |
| `1.10.0-3` | `1.14.0` | `Date` operator. |
| `1.10.0-2` | `1.14.0` | Comparison operators accept multiple operands. |
| `1.10.0-1` | `1.10.0` | `Rational` and `Ln` operators. |
