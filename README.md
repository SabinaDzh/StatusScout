# Проект StatusScout

StatusScout - это telegram-бот, который будет обращаться к API сервиса и узнавать статус вашей работы: взята ли ваша работа на в проверку, проверена ли она, а если проверена — приняли её или вернули на доработку.

## Как запустить проект:

### Клонирование репозитория:

git clone https://github.com/SabinaDzh/StatusScout.git
cd StatusScout

### Cоздание и активирование виртуального окружения:

python -m venv env
source env/bin/activate

### Установка зависимостей из файла requirements.txt:

python -m pip install --upgrade pip
pip install -r requirements.txt

### Выполнение миграции:

python manage.py migrate

### Запуск проекта:

python manage.py runserver

=======
Автор проекта @SabinaDzh
