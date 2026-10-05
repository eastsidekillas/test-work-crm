# Приёмная — мини-CRM агентства

Django 5.2 + DRF + PostgreSQL · Angular 20 + Tailwind 4 + FSD · aiogram 3.

## Возможности

- Вход под учётной записью агентства.
- Получение лидов из Telegram-бота: имя, контакт, запрос.
- Ручное добавление лида.
- Создание тегов, назначение нескольких тегов и снятие.
- Фильтр по одному тегу, пагинация, обновление списка кнопкой.
- Повтор отправки одной Telegram-анкеты не создаёт дубль.

Нет регистрации, ролей, редактирования основных полей и подключения личного Telegram. Незавершённые анкеты хранятся в памяти и сбрасываются при перезапуске бота. Данные CRM хранятся в PostgreSQL. Не масштабируйте бот в несколько экземпляров.

## Размещение на VPS

Нужны Linux VPS, Docker Engine с Compose v2, домен с DNS A-записью на IP сервера и открытые порты 80/443. Если у домена есть AAAA-запись, IPv6 также должен вести на этот VPS. База и API не публикуют отдельные порты. Caddy автоматически получает сертификат, Nginx раздаёт Angular и направляет запросы API в Django.

Перенесите эту папку на сервер и выполните из неё:

```bash
cp .env.example .env
chmod 600 .env
```

Укажите в `.env` свой `DOMAIN` без протокола. Для `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` и `TELEGRAM_API_SECRET` сгенерируйте три разных значения:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Повторите команду трижды и вставьте значения в соответствующие поля. Секреты в браузер не передаются. Не публикуйте `.env`.

Запустите сначала CRM без бота:

```bash
docker compose up -d --build
docker compose ps
docker compose exec backend python manage.py createsuperuser
```

Миграции и сборка статических файлов выполняются сервисом `init`. Его состояние `Exited (0)` нормально. Создайте пользователя интерактивно, запомните логин и пароль. Откройте `https://ВАШ-ДОМЕН/` и войдите. `/admin/` доступен той же учётной записи.

### Подключение бота

1. Создайте бота через `@BotFather` командой `/newbot`.
2. Вставьте его токен в `TELEGRAM_BOT_TOKEN` файла `.env`.
3. Запустите отдельный процесс бота:

```bash
docker compose --profile telegram up -d --build
```

Бот использует long polling; webhook не нужен. Один токен должен использовать только один работающий процесс. При запуске старый webhook этого бота удаляется, накопленные обновления не сбрасываются.

Откройте бота, отправьте `/start`, заполните анкету и нажмите «Отправить заявку». В CRM нажмите «Обновить». Создайте тег, нажмите `+` в колонке тегов нужного лида, выберите тег и сохраните. Нажмите на тег в боковой панели для фильтрации.

### Обновление

Перед изменением схемы БД сделайте резервную копию. Перенесите новые исходники, затем:

```bash
docker compose --profile telegram build
docker compose run --rm init
docker compose --profile telegram up -d
```

Вторая команда применяет миграции до запуска новой версии. Не удаляйте тома PostgreSQL. Команда `docker compose down -v` удалит данные.

### Резервная копия

```bash
mkdir -p backups
chmod 700 backups
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backups/crm.dump
chmod 600 backups/crm.dump
```

Храните копию вне VPS. Восстановление заменяет текущие данные, поэтому сначала остановите приложение:

```bash
docker compose --profile telegram stop bot backend
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < backups/crm.dump
docker compose --profile telegram up -d
```

### Диагностика

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose --profile telegram logs --tail=100 bot
docker compose logs --tail=100 caddy
```

Если браузер не открывает CRM — проверьте DNS, доступность 80/443 и логи Caddy. Если backend нездоров — проверьте логи `init` и доступность PostgreSQL. В endpoint `/api/health/` проверяется соединение с БД. Не публикуйте логи с персональными данными.

## Локальный запуск в Docker

Для просмотра без домена и сертификата используйте дополнительный файл `compose.local.yaml`. В `.env` должны быть заполнены секреты и `DOMAIN=localhost`.

```bash
docker compose -p agency-crm-local -f compose.yaml -f compose.local.yaml up -d --build db init backend web
docker compose -p agency-crm-local -f compose.yaml -f compose.local.yaml exec backend python manage.py createsuperuser
```

Откройте `http://localhost:8080`. Это отдельное окружение с собственными томами. Бот запускается после добавления токена:

```bash
docker compose -p agency-crm-local -f compose.yaml -f compose.local.yaml --profile telegram up -d --build bot
```

Остановка с сохранением данных:

```bash
docker compose -p agency-crm-local -f compose.yaml -f compose.local.yaml down
```

Не используйте локальные настройки на публичном VPS: они включают DEBUG и HTTP cookies. Для VPS запускайте основной compose.yaml.

## Локальная разработка

Нужны Python 3.12+, Node.js 22.12+ или совместимая LTS-версия, npm.

### Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
export DJANGO_DEBUG=1
export DJANGO_SQLITE=1
export TELEGRAM_API_SECRET=local-development-integration-secret
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py createsuperuser
.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

SQLite предусмотрен только для удобства локальной разработки. На VPS используется PostgreSQL. Для локального PostgreSQL уберите `DJANGO_SQLITE`, задайте `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.

### Frontend — второй терминал

```bash
cd frontend
npm ci
npm start
```

Откройте `http://127.0.0.1:4200/`. Angular перенаправляет `/api/` на Django. Не смешивайте `localhost` и `127.0.0.1`, чтобы CSRF и cookies работали в одном origin.

### Bot — третий терминал

```bash
.venv/bin/pip install -r bot/requirements.txt
export TELEGRAM_BOT_TOKEN='ТОКЕН-ВАШЕГО-БОТА'
export TELEGRAM_API_SECRET=local-development-integration-secret
export CRM_API_URL=http://127.0.0.1:8000
.venv/bin/python bot/main.py
```

## Проверки

```bash
DJANGO_DEBUG=1 DJANGO_SQLITE=1 .venv/bin/python backend/manage.py test crm
(cd bot && ../.venv/bin/python -m unittest -v)
```

Для сквозного теста с запущенным локальным Django задайте `CRM_TEST_URL`, `CRM_TEST_SECRET`, `CRM_TEST_USERNAME`, `CRM_TEST_PASSWORD` перед запуском тестов бота. Тест симулирует транспорт Telegram, но использует настоящий aiogram Dispatcher, HTTP API и базу; он добавляет лид и тег.

```bash
cd frontend
npm run build
npx playwright install chromium
```

Для браузерной проверки запустите оба локальных сервера, создайте отдельного пользователя для тестов и передайте его данные:

```bash
E2E_USERNAME=your-test-user E2E_PASSWORD=your-test-password npm run test:e2e
```

Тест создаёт лид и тег в вашей локальной базе. Для установленного Google Chrome можно вместо установки Chromium задать `E2E_CHROME=1`.

## FSD

- `app` — загрузка, маршруты и защита маршрутов.
- `pages` — вход и список лидов.
- `features` — вход, добавление лида, создание и назначение тегов.
- `entities` — Lead, Tag, User и их API.
- `shared` — HTTP-клиент и модальный диалог.

Верхние слои импортируют нижние. `shared` не знает о лидах. Бот создаёт лиды через закрытый Django endpoint. Nginx блокирует этот endpoint для внешних запросов; внутренний запрос дополнительно защищён секретом.

## Материалы задания

- `docs/product.md` — набросок продукта и подход к подключению личного Telegram.
- `docs/retrospective.md` — описание работы в Codex; дополните своими действиями и скриншотами.
- `docs/verification.md` — результаты проверки и ограничения среды.

Живая ссылка и реальный Telegram-сценарий проверяются после размещения на VPS и добавления токена. В репозитории нет реального токена и production-паролей.
