# snapshot_checker

Для работы необходимы модули python3 mysql.connector и paramiko 

Программа ищет сепшоты по заданным параметрам на гипервизорах ESXi

## Настройка:

### Конфиг файл

1. Создаем файл **conn.conf** - это файл конфигурации
2. Добавляем гиперизоры в файл конфигурации

* **[{name}]** - имя гипервизора;
* **host** - IP-адрес хоста;
* **user** - пользователь для подключения по ssh;
* **pass** - пароль для подключения по ssh;
* **percent** - максимальный процент размера снепшота от размера ВМ (сумма размеров всех дисков);
* **count** - максиальное количество снепшотов.

### Mysql (опционально):

1. mysql < script.sql
2. Заносим в конфиг настройки для подключения в MySQL

* **[MYSQL]**
* **HOST** - IP-адрес сервера с базой данных;
* **USER** - пользователь для подключения;
* **PASS** - пароль для подключения;
* **DB** - База данных.

## Ключи запуска:
```
./checker.py [--mysql][--out]
```
* *--mysql* - занесение найденой информации в базу данных;
* *--mysql_out* - вывести информацию из базы данных;
* *--out* - вывести информацию по найденым снепшотам в дружелюбном формате;
* Запуск без ключей - вывод найденных снепшотов в формате списка словарей по всем гиперизорам.
