# FreeVigilanceReduction

Autonomous service for automatic anonymization of personal data in Russian-language text documents.

---

## О проекте

**FreeVigilanceReduction** — это полноценный стек для организации автоматической анонимизации:

* **Python-библиотека** — ядро, реализующее анонимизацию текста.
* **API** — лёгкий HTTP-сервис с эндпоинтами для загрузки документов, опроса статуса задач, получения результатов.
* **Клиентская часть** — HTML/JS-интерфейс, который позволяет загружать файлы (docx, pdf, txt) и получать анонимизированный текст и отчёты.

---

## Структура репозитория

* `/free_vigilance_reduction`
  — Python-библиотека со всеми классами.
* `/api`
  — FastAPI-приложение
  — `routes/` содержит файлы `upload.py`, `status.py`, `results.py`, `download.py`, `profiles.py`
  — `dependencies.py`, `task_manager.py` и вспомогательные утилиты
* `/templates`
  — HTML-шаблон главной страницы
* `/static`
  — CSS и `main.js` для клиентской логики
* `/config`
  — JSON-файлы примеров профилей анонимизации и шаблонов регулярных выражений

---

## Профили анонимизации

Профили хранятся в JSON-файле (по умолчанию `config/profiles.json`) в формате:

* `profile_id`: уникальный идентификатор
* `entity_types`: список кодов сущностей (PER, LOC, ORG, PHONE и т. д.)
* `replacement_rules`: для каждого типа указывается стратегия (набор символов, шаблон, удаление)
* `dictionary_paths`: опциональные словари с путями и флагами включения
* `custom_entity_prompts`: описания для LLM-модуля, если используется языковая модель
* `use_regex`, `use_dictionary`, `use_language_model`: какие методы применять при обнаружении

В каталоге `examples/config` вы найдёте готовый образец профиля.

---

## Как начать

1. **Установка зависимостей**
   Установите необходимые пакеты:

   ```bash
   pip install -r requirements.txt
   ```

2. **Языковая модель**
   Для контекстного анализа используется модель
   [Vikhr-Gemma-2B-instruct](https://huggingface.co/Vikhrmodels/Vikhr-Gemma-2B-instruct).
   Пример по скачиванию есть в `examples/model_download.py`

3. **Настройка профилей**
   Отредактируйте файл `api/config/profiles.json` или возьмите один из примеров из `examples/config`.

4. **Запуск сервера (API)**
   Запустите FastAPI-приложение командой:

   ```bash
   uvicorn api.main:app --reload
   ```

   По умолчанию сервер будет доступен на `http://127.0.0.1:8000/`.

5. **Запуск клиентской части**
   Клиентская часть представляет собой статический HTML/JS, который автоматически подхватывает API сервера. Просто откройте в браузере:

   ```
   python client/app.py
   ```

   — и вы увидите интерфейс для загрузки документов, просмотра результатов и скачивания архивов.

После этого можно выбирать профиль, загружать TXT/DOCX/PDF (PDF автоматически конвертируется в TXT на клиенте) и получать анонимизированные тексты с отчётами прямо в браузере.

---

## Лицензия

Проект распространяется под лицензией **GPL-3.0 license**. Подробнее см. в файле [LICENSE](LICENSE).
