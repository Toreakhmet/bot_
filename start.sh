#!/bin/bash

# Путь к директории проекта
PROJECT_DIR=$(dirname "$0")

# Создаем виртуальное окружение, если оно не существует
if [ ! -d "$PROJECT_DIR/.venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$PROJECT_DIR/.venv"
fi

# Активируем виртуальное окружение
echo "Activating virtual environment..."
source "$PROJECT_DIR/.venv/bin/activate"

# Установка зависимостей
echo "Installing dependencies..."
pip install -r "$PROJECT_DIR/requirements.txt"

# Запуск Docker Compose
echo "Starting Docker Compose..."
docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d

# Выполнение скрипта для базы данных
echo "Running database setup script..."
python "$PROJECT_DIR/create_baza.py"

# Запуск основного скрипта
echo "Running main application..."
python "$PROJECT_DIR/main.py"

echo "All processes started successfully."
