# Metrics

Журнал проекта: `.local/metrics/ledger.yaml`.
Состояние проекта: `.local/project-state.yaml`.

Каталог `.local/` не коммитится. Репозиторий фреймворка хранит только пустые шаблоны `.framework/project-state.yaml` и `.framework/metrics/ledger.yaml`. Идентификатор задачи продукта в эти файлы не записывается.

После каждой принятой задачи дописывается одна строка. На релизе новые строки не создаются: рефлексия сводит журнал.

Любое входящее сообщение открывает ход. `scripts/record-turn.py` на хуке `beforeSubmitPrompt` пишет строку в `.local/metrics/turns.yaml` со статусом `started` и пустыми числами. Хук `stop` дописывает в ту же строку входные, выходные и кэш-токены, `loop_count` и длительность. Текст запроса туда не попадает. Нет поля в хуке — в строке `null`, число не выдумывается. Токены субагентов хук родителя не содержит, поэтому сумма ходов меньше полного счёта. В строку журнала эти суммы переносятся при принятии задачи и только из `turns.yaml`. Пока файла нет, токены, итерации и время в журнале остаются пустыми. Неизвестное число — `null`.

## Строка принятой задачи

Обязательные поля, которые видны из сессии:

- `task` — идентификатор активной задачи;
- `recorded_at` — дата `YYYY-MM-DD`;
- `status` — `accepted`;
- `verification_passed` — `true` или `false`;
- `acceptance_criteria_covered` — сколько критериев закрыто, или `null`;
- `assumptions_invalidated` — сколько допущений опровергнуто, или `null`;
- `missing_requirements_after_implementation` — сколько требований нашлось после реализации, или `null`;
- `context_escalated` — `true` или `false`.

Пока задача не принята, допустима последняя строка с тем же `task`, `status: in_progress` и `verification_passed: null`. Её `recorded_at` не старше `active_task_since`.

## Efficiency

Пока задача идёт, `python3 scripts/record-turn.py --summary` суммирует ходы активной задачи. На принятии те же суммы переносятся в журнал, если каждый ход их содержит. Иначе поле журнала — `null`.

- tokens / completed task — сумма `input_tokens` и `output_tokens` ходов этой задачи
- iterations / accepted task — число ходов в `turns.yaml`
- time-to-accepted-task — сумма `duration_ms`, когда она есть у каждого хода

## Quality

- first-pass acceptance rate
- escaped defects
- reopened tasks
- AC coverage — из `acceptance_criteria_covered`
- verification failures — из `verification_passed: false`

## Context quality

- assumptions created
- assumptions invalidated — из `assumptions_invalidated`
- missing requirements discovered after implementation — из `missing_requirements_after_implementation`
- context escalations — из `context_escalated`
- contradictions discovered

## Closeout

1. Дописать строку в журнал.
2. Не менять `active_task` и `active_task_since`, пока `./scripts/verify.sh` не проходит.
3. Проверка падает, если активная задача новее последней строки или строка про другую задачу.

## Release reflection

1. Свести уже записанные строки журнала. Не опрашивать сессии заново и не заполнять пустые токены догадкой.
2. Сформировать краткую таблицу.
3. Найти повторяемые причины.
4. Каждый полезный вывод превратить в backlog/ADR/rule/test/config/skill.
5. Удалить non-actionable reflection.
