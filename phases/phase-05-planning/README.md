# Фаза 5 — Планирование

![Прогресс](https://img.shields.io/badge/Прогресс-в%20работе-yellow)

## Цель

Построить ресурсно-ограниченное расписание реализации выбранного MVP системы управления результатами тестирования на проникновение.

В качестве масштаба используется сценарий A из Фазы 3: **9 Use Cases, около 1584 чел.-ч**.

## Задачи

| Код | Issue | Работа | Исполнитель |
|---|---|---|---|
| P5-01 | [#47](https://github.com/Redin666/project_management/issues/47) | 20–25 проектных работ | Никита Редин |
| P5-02 | [#48](https://github.com/Redin666/project_management/issues/48) | Состав команды и типы ресурсов | Павел Шатков |
| P5-03 | [#49](https://github.com/Redin666/project_management/issues/49) | Ресурсные требования работ | Павел Шатков |
| P5-04 | [#50](https://github.com/Redin666/project_management/issues/50) | Связи предшествования | Никита Редин |
| P5-05 | [#51](https://github.com/Redin666/project_management/issues/51) | Детерминированные эвристики | Никита Редин |
| P5-06 | [#52](https://github.com/Redin666/project_management/issues/52) | Анализ эвристик | Владислав Полищук |
| P5-07 | [#53](https://github.com/Redin666/project_management/issues/53) | Случайные варианты и выбор лучшего | Никита Редин |
| P5-08 | [#54](https://github.com/Redin666/project_management/issues/54) | Календарь 8 ч / 40 ч | Павел Шатков |
| P5-09 | [#55](https://github.com/Redin666/project_management/issues/55) | Визуальный план / Gantt | Владислав Полищук |
| P5-10 | [#56](https://github.com/Redin666/project_management/issues/56) | Итоговый анализ | Владислав Полищук |

## Модель проекта

Реализация декомпозирована на **22 работы**. Ресурсная модель основана на выводах P3-07:

- Backend — 2 специалиста;
- Frontend — 1 специалист;
- QA / DevOps / аналитика — 1 специалист.

Суммарная ресурсная трудоёмкость 22 работ составляет **198 человеко-дней = 1584 человеко-часа**, что согласуется с выбранным сценарием A Фазы 3.

## Каталоги

- [P5-01 — декомпозиция](project-decomposition/README.md)
- [P5-02 — ресурсы](resources/README.md)
- [P5-03 — ресурсные требования](resource-requirements/README.md)
- [P5-04 — предшествование](precedence/README.md)
- [P5-05 — эвристики](heuristics/README.md)
- [P5-06 — анализ эвристик](heuristic-analysis/README.md)
- [P5-07 — случайный поиск](random-search/README.md)
- [P5-08 — календарный план](calendar-plan/README.md)
- [P5-09 — Gantt](gantt/README.md)
- [P5-10 — выводы](conclusions/README.md)

## Предварительный результат планирования

Лучшие детерминированные правила и случайный поиск дают **89 рабочих дней** при заданных ресурсах. При старте в понедельник **23.11.2026** и календаре 5×8 часов расчётное окончание — **25.03.2027**, то есть около **17,8 рабочей недели**.
