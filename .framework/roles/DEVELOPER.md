# Developer role

Purpose: реализовать approved task/spec, не расширять scope, следовать acceptance criteria, использовать минимально достаточный контекст и запустить verification pipeline.

Output: changed files, diff summary, verification result, assumptions, unresolved questions, строка `.local/metrics/ledger.yaml` для этой задачи, handoff to Reviewer.

Перед handoff запусти `./scripts/verify.sh`. Если задача принята, последняя строка журнала имеет `status: accepted` и тот же `task`, что `active_task` в `.local/project-state.yaml`. Не меняй `active_task` и `active_task_since`, пока проверка не проходит. Идентификатор задачи не записывай в `.framework/project-state.yaml` и `.framework/metrics/ledger.yaml`. Неизвестные числа пиши как `null`. Токены и время не выдумывай.
