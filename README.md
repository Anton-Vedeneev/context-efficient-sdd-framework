# Context-Efficient SDD Framework

Мини-фреймворк для разработки проектов с AI-агентом в Cursor.

## Цель

Упростить агенту работу, снизить расход токенов, уменьшить число итераций во время разработки и сократить количество дефектов, обнаруживаемых после релиза.

Фреймворк достигает этого через:

- управляемый контекст вместо полного чтения репозитория;
- формализованный профиль человека и матрицу полномочий;
- один выбранный workflow adapter: OpenSpec **или** Superpowers;
- спецификацию, acceptance criteria и traceability до реализации;
- ролевой relay-процесс Architect → Developer → Reviewer → QA;
- единый verification pipeline;
- post-release метрики, рефлексию и перевод полезных выводов в backlog/ADR/rules;
- запрет на накопление мусорного контекста.

## Как начать

1. Клонируйте репозиторий и откройте его в Cursor.
2. Напишите агенту: `Начинаем`.
3. Если у вас уже есть preprompt — передайте его агенту.
4. Если вы не знаете, что такое preprompt, агент должен **сразу** запустить короткий bootstrap-опрос и сам сформировать нужные артефакты.
5. После bootstrap выберите **один** workflow: OpenSpec или Superpowers.
6. Перед реализацией агент обязан выполнить intake/decomposition проекта и архитектурный grooming.

## Что Cursor обязан понять при старте

Cursor работает **внутри структурированной системы управления контекстом**. Он не должен заменять процесс своим собственным workflow.

Стартовый порядок:

1. прочитать `.framework/CORE.md`;
2. прочитать `.framework/framework.yaml`;
3. прочитать `.framework/BOOTSTRAP.md`;
4. проверить наличие `.local/human-profile.yaml`;
5. если профиль отсутствует — запросить preprompt или запустить опросник;
6. проверить, выбран ли adapter;
7. только после bootstrap переходить к project intake.

## Основные законы

1. Не тащи знания в контекст заранее — доставляй их к моменту принятия решения.
2. Не позволяй шуму становиться памятью проекта.
3. Не позволяй агенту менять систему, которая ограничивает самого агента.
4. Fact ≠ Inference ≠ Decision ≠ Unknown.
5. Изменение scope сначала меняет spec/plan, затем код.
6. Reflection не является knowledge base: полезный вывод превращается в backlog/ADR/rule/test, остальное удаляется.

## Контекстные режимы

- `efficient` — минимально достаточный контекст;
- `extended` — расширенный бюджет для сложных задач;
- `unrestricted` — временно разрешает максимально широкий контекст и намеренно противоречит основной идее экономии токенов.

Агент может **предложить** escalation, но не должен сам переключать режим.

## Verification

Проект должен предоставить единый entry point:

```bash
./scripts/verify.sh
```

## Метрики

После релиза анализируются как минимум:

- tokens / completed task;
- iterations / accepted task;
- time-to-accepted-task;
- first-pass acceptance rate;
- escaped defects;
- reopened tasks;
- acceptance criteria coverage;
- invalid assumptions;
- missing requirements found after implementation;
- context escalations.

Результат рефлексии должен либо стать конкретным изменением системы, либо быть удалён.
