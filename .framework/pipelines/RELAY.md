# Relay Pipeline v0.1

Architect → Developer → Reviewer → QA → Release Gate

## Isolation rule

Следующая роль получает spec/task, AC, diff/evidence, assumptions, unresolved questions, ссылку на строку журнала метрик и релевантные context refs. Она не получает полный reasoning/историю предыдущей роли и не получает весь журнал.

## Goal

Снизить confirmation bias, контекстный шум, token duplication и повторное чтение нерелевантной истории.

## Release Gate

1. Developer дописал в `.framework/metrics/ledger.yaml` строку принятой задачи и не сдвигал `active_task`, пока `./scripts/verify.sh` не прошёл.
2. Reviewer сверяет diff с acceptance criteria и не закрывает ревью без этой строки.
3. QA не выдаёт «готово», если строки нет или verify.sh завершился с кодом 1.
4. Рефлексия релиза сводит уже записанные строки. Новую строку на релизе не создаёт.
