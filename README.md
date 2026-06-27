# VK Checker: сбор данных и бесплатная эвристическая фильтрация

`vk_checker` — Python-приложение для массового обхода сообществ ВКонтакте из Google Таблицы. Проект больше не классифицирует сообщества через внешний AI. Его задача — собрать качественные данные, посчитать эвристический score и оставить для дальнейшей обработки BotHelp AI только кандидатов классов A и B.

## Новая схема работы

```text
VK
↓
Playwright
↓
Parser
↓
Heuristic Filter
↓
Google Sheets
↓
Candidate Export
↓
BotHelp AI — будет подключён позже
```

## Что собирается

- ссылка;
- название;
- описание;
- статус;
- количество подписчиков;
- ссылки из описания и найденного текста;
- ссылки из меню;
- контакты;
- услуги;
- товары;
- закреплённый пост;
- последние 5 постов;
- телефоны;
- email;
- сайт;
- упоминания Telegram;
- упоминания WhatsApp;
- упоминания курсов, обучения, вебинаров, наставничества, консультаций, марафонов и интенсивов;
- внешние ссылки.

## Эвристическая фильтрация

Все правила находятся в `prefilter_rules.yaml`:

- `positive_keywords` — положительные ключевые слова и веса;
- `negative_keywords` — отрицательные ключевые слова и веса;
- `required_patterns` — положительные regex-паттерны и веса;
- `forbidden_patterns` — отрицательные regex-паттерны и веса;
- `thresholds.high` и `thresholds.medium` — пороги классов.

Классы кандидатов:

- `A` — высокая вероятность инфобизнеса;
- `B` — сомнительные, стоит передать в BotHelp AI;
- `C` — низкая вероятность, не отправлять в AI.

## Установка Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
```

## `.env`

```env
GOOGLE_SHEET_ID=your-google-sheet-id
GOOGLE_SERVICE_ACCOUNT=./service-account.json
HEADLESS=false
MAX_CONCURRENT=2
VK_STORAGE_STATE=.vk-profile
INPUT_SHEET_NAME=Лист1
INPUT_COLUMN=A
START_ROW=2
REQUEST_TIMEOUT=60
LOG_LEVEL=INFO
```

## `config.yaml`

```yaml
project:
  progress_interval: 1000
  checkpoint_interval: 100
  artifacts_dir: artifacts
  cache_path: .vk_checker_cache.sqlite3
  checkpoint_path: checkpoint.json
  export_dir: exports
scraping:
  navigation_timeout_ms: 30000
  max_links: 80
  max_posts: 5
  max_text_chars: 8000
rate_limits:
  playwright_rpm: 120
  google_sheets_rpm: 60
  jitter_ms: 350
monitoring:
  error_spike_threshold: 0.2
prefilter:
  rules_path: prefilter_rules.yaml
```

## Google Таблица

В столбце `A` должны быть ссылки на VK-сообщества. Первая строка — заголовок, данные начинаются со строки `START_ROW`.

Приложение добавляет столбцы:

- `Score`;
- `Matched positive keywords`;
- `Matched negative keywords`;
- `Candidate class`;
- `Collected text size`;
- `Последняя проверка`;
- `Статус`;
- `Ошибка`.

## Первый запуск

Сначала авторизуйтесь во VK через видимый браузер:

```powershell
python -m vk_checker --dry-run --range 2-2
```

Затем проверьте 20 строк:

```powershell
python -m vk_checker --resume --range 2-21 --workers 2 --stats --export-candidates
```

## Постепенное увеличение объёма

500 строк:

```powershell
python -m vk_checker --resume --range 2-501 --workers 2 --stats --export-candidates
```

Вся таблица — только после успешной проверки малых диапазонов:

```powershell
python -m vk_checker --resume --workers 2 --stats --export-candidates
```

## Экспорт

После обработки создаются:

- `exports/results.csv`;
- `exports/results.xlsx`;
- `exports/errors.csv`;
- `exports/statistics.json`;
- `exports/high_probability.csv`;
- `exports/medium_probability.csv`;
- `exports/low_probability.csv`;
- `exports/high_probability.xlsx`;
- `exports/medium_probability.xlsx`;
- `exports/low_probability.xlsx`.

Команда `--export-candidates` дополнительно создаёт:

- `exports/candidates_for_bothelp.csv`.

Этот файл содержит только группы `A` и `B`.

## Ошибки и диагностика

- `logs/app.log` — общий лог;
- `logs/errors.log` — ошибки;
- `artifacts/errors/*.html` и `artifacts/errors/*.png` — HTML и screenshot страницы при ошибке;
- `checkpoint.json` — состояние продолжения;
- `.vk_checker_cache.sqlite3` — кэш результатов эвристики.

## Проверки разработки

```powershell
python -m compileall -q vk_checker tests
ruff check .
mypy vk_checker
pytest -q
python -m vk_checker --help
```

## Валидация качества правил

Создать случайную выборку для ручной разметки:

```powershell
python -m vk_checker validate_rules --validation-count 200 --range 2-5000 --workers 2
```

Команда создаст `exports/validation.xlsx` со столбцами `url`, `title`, `description`, `score`, `candidate_class`, `matched_positive_keywords`, `matched_negative_keywords`, `Human verdict`.

Заполните `Human verdict` вручную значениями:

- `Да` — сообщество действительно относится к инфобизнесу / онлайн-образованию;
- `Нет` — не относится;
- `Не уверен` — исключить из расчёта метрик.

После заполнения запустите ту же команду повторно:

```powershell
python -m vk_checker validate_rules --validation-file exports/validation.xlsx --quality-report exports/quality_report.html
```

Будут рассчитаны `Precision`, `Recall`, `F1-score`, `Accuracy`, `Confusion Matrix`, ложноположительные и ложноотрицательные ошибки. Также будет создан HTML-отчёт `exports/quality_report.html` с графиками распределения score, классов и рекомендациями по улучшению правил.
