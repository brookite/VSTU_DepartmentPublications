## DepartmentPublications
Система, позволяющая отслеживать публикации студентов, магистрантов, аспирантов, сотрудников ВолгГТУ.   
Принцип работы системы состоит в следующем:   
- Система автоматически получает информацию о кафедрах и факультетах ВУЗа
- Администратор системы вносит в локальную базу данных автора, привязывает его к кафедре
- Система через определенные промежутки времени (см. настройки планирования в системе) обновляет из библиотеки ВолгГТУ информацию о всех авторах
- Если обнаруживаются новые публикации, они вносятся в локальную базу данных и система сообщает о новых публикациях у автора


Система имеет API для работы с локальной базы данных системы 


### Системные требования:
1. Наличие Docker в системе (с плагином docker compose)
2. Если Docker отсутствует, развернуть систему можно непосредственно на машине, для этого потребуется
   - Одна из поддерживаемых баз данных PostgreSQL/MySQL/MariaDB
   - Python 3.10 и выше

### Установка системы

#### Docker (рекомендуется)
1. Установить Docker на свою машину/сервер
2. Создать в папке проекта файл с названием `.env` c содержимым имени и пароля для создаваемой базы данных    
Пример:
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
DJANGO_SUPERUSER_PASSWORD=admin
```
3. Если необходимо подключить поддержку рассылки по электронной почте, создайте файл `prod.env`. Пример содержимого [в файле](example.env)
4. Перейти в терминале/командной строке в коренную папку системы
5. Выполнить развертывание и дождаться запуска в фоне
```bash
# docker compose up -d
```
Для остановки системы
```bash
# docker compose down
```
6. В системе автоматически будет создан аккаунт администратора с именем `admin` и паролем, который вы указали в переменной `DJANGO_SUPERUSER_PASSWORD`

#### Локальная машина/сервер
1. Убедитесь, что установлена одна из допустимых баз данных
2. Создайте в корне проекта файл `prod.env` (для DEBUG режима `dev.env`)
3. Укажите для него содержимое со своими входными данными, согласно примеру  
Пример:
```env
DB_ENGINE=postgresql
DB_USER=user
DB_PASSWORD=admin
DB_HOST=localhost
```
Для переменной `DB_ENGINE` допустимыми значениями являются `postgresql`, `mysql`, `mariadb`
Пример полного содержимого приведен [в файле](example.env)
4. Запустите следующие команды в корне проекта
```bash
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```
5. Задайте имя и пароль для администратора сайта
6. Запустите параллельно две команды
```bash
python manage.py runscript autoupdate_server
```
```bash
python manage.py runserver 0.0.0.0:8000
```
7. Система будет доступна по адресу localhost:8000

> Учтите, что запуск в режиме production требует наличия сервера (например, nginx) для обработки статических файлов. Из-за их отсутствия сайт не будет работать. Руководство по настройке сервера для статических файлов здесь не приводится

### Прочие замечания
> restart.sh и restart.bat предназначены для перезапуска сервера в Docker, они не будут запускаться внутри контейнера