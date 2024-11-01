# Сервис обмена мгновенными сообщениями

## Описание проекта

Проект представляет собой сервис для обмена мгновенными сообщениями между пользователями в реальном времени. Он включает веб-интерфейс, API для отправки и получения сообщений, а также систему уведомлений через Telegram-бота. Сервис построен с использованием FastAPI, Python и поддерживает асинхронную обработку запросов для высокой производительности.

---

## Функциональность

- **Регистрация и аутентификация**:
  - Регистрация новых пользователей.
  - Вход и авторизация через JWT.

- **Отправка и получение сообщений**:
  - Обмен сообщениями в режиме реального времени через WebSocket.
  - Хранение истории переписки между пользователями.

- **Telegram-уведомления**:
  - Уведомления через Telegram-бота при получении новых сообщений, если пользователь оффлайн.

- **Простой веб-интерфейс**:
  - Регистрация, вход в систему, отправка и получение сообщений.

---

## Технологический стек

- **Язык и фреймворк**: Python 3.10+, FastAPI для API и WebSocket.
- **Асинхронность**: async/await для работы с API и WebSocket.
- **Базы данных**:
  - PostgreSQL для хранения пользователей и сообщений.
  - Redis для кэширования и сессий.
- **Telegram Bot**: Aiogram.
- **ORM**: SQLAlchemy с Alembic для миграций.
- **Фоновые задачи**: Celery для отправки уведомлений через Telegram бота.
- **Контейнеризация**: Docker и Docker Compose.
- **Обратное проксирование**: Nginx.

---

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Kylemerian/real-time-web-chat.git
cd real-time-web-chat
```

## 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта и добавьте следующие параметры:

```env
DB_HOST=<Адрес_БД>
DB_PORT=<Порт_для_БД>
DB_NAME=<Название_БД>
DB_USER=<Пользователь_БД>
DB_PASS=<Пароль_БД>
SECRET_HASH=<Хэш_для_JWT>
TGBOTTOKEN=<Ваш_Telegram_бот_токен>
REDIS_HOST=<Адрес_Redis>
```
## 3. Запуск проекта с Docker

Проект поддерживает запуск с помощью Docker Compose. Чтобы развернуть все сервисы, выполните команду:

```bash
docker-compose up --build
```
Эта команда запускает следующие компоненты:

- FastAPI сервер для API и WebSocket.
- Redis для кэширования и хранения сессий.
- PostgreSQL для базы данных.
- Celery для фоновых задач.
- Nginx в роли обратного прокси-сервера.
- Telegram-бот для отправки уведомлений.

## 4. Применение миграций базы данных

Чтобы применить миграции базы данных, выполните:

```bash
docker-compose exec web alembic upgrade head
```

## Использование

### Веб-интерфейс

#### Регистрация и вход:
- Откройте браузер и перейдите на [http://0.0.0.0](http://0.0.0.0)
- Зарегистрируйтесь или выполните вход.

#### Отправка и получение сообщений:
- Обменивайтесь сообщениями с другими пользователями.
- Сообщения доставляются в режиме реального времени.

#### Telegram-уведомления:
- Telegram-бот уведомит вас о новых сообщениях, если вы не в сети.
- Для активации уведомлений свяжите свой `chat_id` с учетной записью.

### Основные API эндпоинты

API-документация доступна по адресу `/docs` (Swagger UI).

#### POST запросы

- `/login`: Аутентификация пользователя.
- `/register`: Регистрация нового пользователя.
- `/setTgId`: Установка Telegram chat_id для пользователя.
- `/addChat`: Добавление нового чата.

#### GET запросы

- `/getUsers`: Получение списка пользователей.
- `/app`: Доступ к основному приложению.
- `/getChats`: Получение списка чатов.
- `/chat/{chat_id}`: Получение информации о чате по ID.

### Команды для разработки и отладки

- Запуск контейнеров: `docker-compose up --build`
- Остановка контейнеров: `docker-compose down`
- Просмотр логов: `docker-compose logs -f`
- Пересборка контейнеров: `docker-compose up --build`

### Особенности реализации

- Асинхронность: Использование `async/await` во всех эндпоинтах для оптимизации производительности.
- WebSocket для реального времени: Поддержка реального времени для обмена сообщениями.
- Celery для фоновых задач: Уведомления через Telegram-бота.
- JWT-аутентификация: Защищенный доступ к API через JWT-токены.
