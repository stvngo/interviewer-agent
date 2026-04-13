# Testing boundaries
## 10.1 Service tests
Test:
- session creation
- question assignment
- transcript persistence
- code event persistence
- scoring aggregation
- report persistence

## 10.2 Node tests
Test:
- node input -> state output
- node side effects
- event emissions
- policy correctness

## 10.3 Graph transition tests
Test:
- state routes to correct next node
- question advancement works
- hint path works
- pause/resume works
- round completion works

## 10.4 Contract tests
Test:
- event envelope validation
- idempotency rules
- agent structured outputs
- Pydantic schema compatibility

## 10.5 End-to-end simulation tests
Test:
- one behavioral round
- one coding round
- hint flow
- report generation flow