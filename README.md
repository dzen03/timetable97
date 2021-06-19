# Расписание для Лицея 97 в Telegram.

## Установка
1. ```git clone https://github.com/dzen03/timetable97.git```
2. ```pip install -r requirments.txt```
3. Установить LibreOffice (https://www.libreoffice.org/download/download/)
4. Создать бота в Telegram (https://t.me/botfather)
5. Возможно нужно будет добавить папку с расписанием на свой Гугл диск
6. Выбрать систему (я использовал linux, но на windows **должно** работать): 

### a. Linux:
7. Установить, настроить rclone (https://github.com/rclone/rclone)

### b. Windows
7. Установить, настроить Google Drive для компьютера (https://www.google.com/drive/download/)


## Настройка
1. Main.py:
    * строка 94 изменить версию для linux, а для windows нужно указать путь до него
    * строка 146 удалить строку для windows (диск сам себя обновляет)
2. variables.py:
    * вставить токен от бота
    * указать путь до синхронизируемой папки с расписанием
3. g.sh (linux только):
    * для linux: указать путь до синхронизируемой папки с расписанием


## Возможности
* Можно очистить хэш с помощью ```clear.py```
* Если добавить администраторов в ```строке 17 Bot.py```, то они смогут обновлять расписание удаленно с помощью ```/refresh```


P.S.
Со мной можно связаться через телеграм: [@dzen03](https://t.me/dzen03)