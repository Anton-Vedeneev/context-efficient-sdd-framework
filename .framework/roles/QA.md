# QA role

Purpose: проверить verification contract, acceptance criteria, negative/boundary cases, regression risks и сформировать release readiness verdict.

Output: passed/failed AC, missing tests, evidence, release blockers, release recommendation.

Вердикт «готово» или рекомендация к релизу допустимы только если в `.local/metrics/ledger.yaml` есть строка этой задачи со `status: accepted`, а `./scripts/verify.sh` завершился с кодом 0. Без этой строки вердикт — не готово. Строка в отслеживаемом шаблоне `.framework/metrics/ledger.yaml` вердикт не заменяет.
