# Фаза 4 — Прогнозирование

![Прогресс](https://img.shields.io/badge/Прогресс-в%20работе-yellow)

## Цель

Спрогнозировать срок выполнения работ Фазы 5 двумя независимыми Монте-Карло моделями на основе истории работы команды.

## Задачи

| Код | Issue | Работа | Исполнитель |
|---|---|---|---|
| P4-01 | [#41](https://github.com/Redin666/project_management/issues/41) | Декомпозиция Фазы 5 | Никита Редин |
| P4-02 | [#42](https://github.com/Redin666/project_management/issues/42) | Трёхточечные оценки P5-01…P5-10 | Павел Шатков |
| P4-03 | [#43](https://github.com/Redin666/project_management/issues/43) | Недельная история throughput и человеко-часов | Никита Редин |
| P4-04 | [#44](https://github.com/Redin666/project_management/issues/44) | Монте-Карло по throughput | Никита Редин |
| P4-05 | [#45](https://github.com/Redin666/project_management/issues/45) | Монте-Карло по человеко-часам | Павел Шатков |
| P4-06 | [#46](https://github.com/Redin666/project_management/issues/46) | Сравнение моделей и вывод | Владислав Полищук |

## Порядок выполнения

1. P4-01 формирует список задач Фазы 5.
2. P4-02 оценивает их по трём точкам.
3. P4-03 формирует два эмпирических недельных распределения.
4. P4-04 и P4-05 выполняются независимо.
5. P4-06 сравнивает уже готовые прогнозы.

## Каталоги

- [P4-01 — декомпозиция](decomposition/README.md)
- [P4-02 — трёхточечные оценки](three-point-estimates/README.md)
- [P4-03 — история](history/README.md)
- [P4-04 — модель throughput](monte-carlo-throughput/README.md)
- [P4-05 — модель человеко-часов](monte-carlo-hours/README.md)
- [P4-06 — сравнение](comparison/README.md)

## Текущий расчёт

- модель 1: медиана **4 недели**, **P80 = 5 недель**;
- модель 2: медиана **9 недель**, **P80 = 13 недель**.
