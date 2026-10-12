# Superpowers Adapter

Status: closeout подключён. Остальная карта skills по-прежнему не расписана.

Используется, если `workflow.adapter: superpowers`.

- Superpowers — единственный выбранный workflow.
- Framework не должен параллельно создавать OpenSpec-структуру.
- Core concepts framework остаются неизменными.
- Adapter отвечает за перевод core workflow в Superpowers conventions.

## Завершение задачи

Superpowers считает задачу законченной, когда проверка прошла. Для framework этого мало.

Перед финальным ответом по задаче, в том же месте, где skill verification-before-completion требует доказательство проверки:

1. Дописать одну строку в `.framework/metrics/ledger.yaml` по `.framework/metrics/METRICS.md`.
2. Запустить `./scripts/verify.sh` из корня репозитория фреймворка.
3. Не объявлять задачу принятой и не менять `active_task` / `active_task_since`, пока скрипт не завершился с кодом 0.

Навык, который просит коммит или завершение ветки, не заменяет эту строку. Релизная рефлексия только сводит журнал.

TODO v0.2: mapping остальных skills, planning lifecycle, implementation/review mapping.
