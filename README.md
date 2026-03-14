# GrowShowcase

---

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-Telegram%20bot-2CA5E0?logo=telegram)
![FastAPI](https://img.shields.io/badge/FastAPI-webhook%20service-009688?logo=fastapi)
![Tortoise ORM](https://img.shields.io/badge/Tortoise%20ORM-database-6A5ACD)
![Redis](https://img.shields.io/badge/Redis-state%20storage-DC382D?logo=redis)
![Stripe](https://img.shields.io/badge/Stripe-payments-635BFF?logo=stripe)
![Cryptomus](https://img.shields.io/badge/Cryptomus-crypto%20payments-2F6BFF)
![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?logo=docker)
![Status](https://img.shields.io/badge/status-in%20development-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

**Инструменты разработки:**

![Aerich](https://img.shields.io/badge/migrations-aerich-7A4CC2)
![Gunicorn](https://img.shields.io/badge/server-gunicorn-499848)
![Uvicorn](https://img.shields.io/badge/ASGI-uvicorn-4B8BBE)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions)
![Docker Compose](https://img.shields.io/badge/orchestration-Docker%20Compose-2496ED?logo=docker)

---

> Telegram-витрина в формате двуязычного бота с каталогом, корзиной, оформлением заказов, административной панелью и интеграцией онлайн-оплаты через Stripe и Cryptomus.

## Обзор проекта

`GrowShowcase` — это портфолио-проект на Python, который объединяет Telegram-бота для пользовательских и административных сценариев с FastAPI-сервисом для обработки webhook-событий и маршрутов, связанных с оплатой.

Проект демонстрирует практический сценарий Telegram-витрины: пользователь может просматривать каталог, добавлять товары в корзину, оформлять заказ, выбирать способ оплаты, просматривать историю заказов и читать отзывы. Со стороны администратора реализованы управление товарами, обработка заказов, просмотр статистики и экспорт данных в CSV.

Репозиторий демонстрирует реальные backend-навыки: архитектуру Telegram-бота, сценарии на основе конечных состояний, работу с ORM, webhook-интеграции, развёртывание через Docker и подключение платёжных шлюзов.

## Возможности

- Двуязычный интерфейс Telegram-бота
- Каталог товаров с пагинацией и карточками
- Корзина и оформление заказов
- История заказов пользователя
- Раздел отзывов с поддержкой изображений
- Административное управление товарами
- Управление заказами и обновление их статусов
- Просмотр статистики и экспорт заказов в CSV
- Поддержка Telegram webhook
- Интеграция оплаты через Stripe и Cryptomus
- Redis для хранения состояний пользователя и служебных данных
- Docker и Docker Compose для развёртывания

## Технологический стек

- **Python**
- **Aiogram** для разработки Telegram-бота
- **FastAPI** для веб-сервиса и обработки webhook-запросов
- **Tortoise ORM** для работы с моделями и базой данных
- **Aerich** для управления миграциями
- **Redis** для хранения состояний и служебных данных
- **Stripe SDK** для приёма онлайн-платежей картой
- **Cryptomus** для приёма онлайн-платежей криптовалютой
- **httpx** для взаимодействия с внешними API
- **Gunicorn + Uvicorn** для запуска веб-приложения
- **Docker / Docker Compose** для контейнеризации и развёртывания
- **GitHub Actions** для автоматизации деплоя на VPS

## Архитектура

Проект разделён на две основные части выполнения.

### 1. Часть Telegram-бота

Бот отвечает за:

- пользовательскую навигацию
- просмотр каталога
- работу с корзиной
- сценарий оформления заказа
- историю заказов
- административные сценарии

Основная точка входа инициализирует бота, диспетчер, базу данных, middleware локализации и маршрутизаторы.

### 2. Веб-сервис

FastAPI-приложение отвечает за:

- приём Telegram webhook
- маршруты перенаправления после успешной и отменённой оплаты
- обработку Stripe webhook
- обработку Cryptomus webhook
- серверные маршруты, связанные с оплатой

### Слой данных

Слой данных построен вокруг следующих сущностей:

- `User`
- `UserLocale`
- `Product`
- `Order`
- `OrderItem`
- `Cart`
- `Review`

Заказы формируются из текущего состояния корзины, а позиции заказа сохраняются отдельно, чтобы фиксировать снимок данных на момент оформления.

## Структура проекта

```text
config_data/        # конфигурация приложения и инициализация основных компонентов
database/           # модели, подключение к базе данных и операции с данными
handlers/           # обработчики пользовательских и административных сценариев
keyboards/          # клавиатуры и навигация Telegram-бота
states/             # состояния пошаговых пользовательских сценариев
services/           # сервисный слой и локализация
payments/           # логика работы с платёжными системами
utils/              # вспомогательные функции
web/                # FastAPI-сервис для webhook и платёжных событий
migrations/         # миграции базы данных
.github/workflows/  # автоматизация развёртывания
```

## Установка

### Требования

- Python 3.12+
- Redis
- Настроенные переменные окружения
- Docker / Docker Compose для контейнерного запуска

### Клонирование репозитория

```bash
git clone https://github.com/0xPrecision/Gr_showcase.git
cd GrowShowcase
```

### Создание виртуального окружения

```bash
python -m venv .venv
source .venv/bin/activate
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка

Проект использует переменные окружения для настройки бота, подключения к базе данных, Redis, конфигурации webhook и платёжных интеграций.

### Основные переменные окружения

```env
TELEGRAM_BOT_TOKEN=...
ADMIN_IDS=123456789,987654321

DATABASE_URL=sqlite:///data/shop.db
REDIS_URL=redis://redis:6379/0

BOT_USERNAME=your_bot_username
TELEGRAM_WEBHOOK_URL=https://your-domain.example
TELEGRAM_WEBHOOK_SECRET=super_secret_value

PAY_SUCCESS_URL=https://your-domain.example/pay/success
PAY_CANCEL_URL=https://your-domain.example/pay/cancel
PAY_FLOW_SECRET=another_secret

STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

CRYPTOMUS_MERCHANT_ID=...
CRYPTOMUS_API_KEY=...
CRYPTOMUS_BASE_URL=https://api.cryptomus.com

AERICH_AUTO_UPGRADE=false
INIT_DB_ALLOW_GENERATE=false
BACKUP_BEFORE_MIGRATE=true
```

## Запуск проекта

Репозиторий поддерживает запуск как в режиме опроса Telegram API для бота, так и в режиме отдельного веб-сервиса.

### Запуск Telegram-бота

```bash
python -m main
```

### Запуск FastAPI-сервиса

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 web.main:app
```

### Запуск через Docker Compose

```bash
docker compose up -d --build
```

### Запуск миграций через Aerich

```bash
docker compose --profile cli run --rm aerich upgrade
```

## Примеры использования

### Для пользователя

Бот позволяет просматривать каталог, добавлять товары в корзину, оформлять заказ, выбирать способ оплаты и отслеживать историю заказов.

### Для администратора

Административная часть позволяет управлять каталогом, редактировать товары, обрабатывать заказы, обновлять их статусы, экспортировать данные в CSV и управлять отзывами.

## База данных и хранение

По умолчанию контейнерная конфигурация использует SQLite в качестве основной базы данных приложения и Redis для хранения состояний и временных служебных данных.

### Основные сущности

- **User**: пользователь Telegram
- **UserLocale**: язык интерфейса
- **Product**: товар каталога
- **Cart**: корзина пользователя
- **Order**: оформленный заказ
- **OrderItem**: товары, входящие в заказ
- **Review**: отзывы с изображениями

По умолчанию проект работает с SQLite, но при необходимости может быть адаптирован под PostgreSQL.

## Интеграции

### Telegram Bot API

Обеспечивает работу пользовательской и административной части бота, обработку изображений, кнопочную навигацию и пошаговые сценарии взаимодействия.

### Stripe

Отвечает за создание платёжных сессий и подтверждение оплаты через webhook.

### Cryptomus

Используется для выставления счетов в криптовалюте и отслеживания статусов оплаты.

## Развёртывание

Для запуска и развёртывания проекта в репозитории предусмотрены:

- `Dockerfile`
- `docker-compose.yml`
- `GitHub Actions workflow`

Проект ориентирован на развёртывание на VPS по SSH с использованием отдельного серверного скрипта.

Docker Compose поднимает отдельные сервисы для Telegram-бота, веб-сервиса, Redis и выполнения миграций базы данных.

## Заключение

GrowShowcase — это портфолио-проект, который демонстрирует практический подход к разработке Telegram-ботов с каталогом, оформлением заказов, административной частью, веб-сервисом для webhook и интеграцией платёжных систем.

Проект показывает умение проектировать структуру приложения, разделять зоны ответственности, работать с базой данных, внешними сервисами и готовить решение к развёртыванию в контейнерной среде.

## Контакты

- Telegram: [@OxPrecision](https://t.me/OxPrecision)
- Email: wrkfrvr@gmail.com

---

© 2025 Nikita OxPrecision. All rights reserved.