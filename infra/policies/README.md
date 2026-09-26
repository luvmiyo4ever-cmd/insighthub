# Policy tests

The positive fixture must pass. The negative fixture must fail with at least
one denial; its non-zero exit is asserted by the verification command rather
than hidden with a skip or soft-fail.

```powershell
conftest test -p infra/policies infra/policies/tests/positive-plan.json
$negativeExit = 0
conftest test -p infra/policies infra/policies/tests/negative-plan.json
$negativeExit = $LASTEXITCODE
if ($negativeExit -ne 1) { throw "Expected negative fixture to fail with exit code 1; got $negativeExit" }
```
