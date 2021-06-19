import datetime
import hashlib
import os
import pickle
import subprocess
import re

from os import listdir

from wand.image import Image

# from os.path import isfile, join
from Bot import write_to_all_users
from misc_functions import next_day

from variables import path_doc

path_app = os.path.dirname(os.path.realpath(__file__)) + '/'  # current path

today_hash = ''
tomorrow_hash = ''


def write_to_file(file_to_write, message):
    fh = open(file_to_write, 'a')
    fh.write(message)
    fh.close()


def path_to_term():
    files = listdir(path_doc)
    files = sorted([i for i in files if i[0].isdigit()])[::-1]
    return files[0] + "/"


def path_to_folders(a):
    dt = datetime.datetime.now() + datetime.timedelta(days=a)

    files = listdir(path_doc + path_to_term())

    is_first_week_of_term = True

    for fl in files:
        if '.doc' not in fl:
            is_first_week_of_term = False
            break

    if is_first_week_of_term:
        return ""  # there is no folders

    files = sorted(files)[:-3:-1]  # use only three previous weeks
    for fl in files:
        start_and_end = re.findall('.+([\\d]+).*-([\\d]+)', fl)
        start = int(start_and_end[0][0])
        end = int(start_and_end[0][1])

        if start <= dt.day <= end:  # check if current date between start and end of the week
            return fl + "/"

    return False


def path_to_files(a):
    dt = datetime.datetime.now() + datetime.timedelta(days=a)

    if not path_to_folders(a):
        return False

    files = listdir(path_doc + path_to_term() + path_to_folders(a))

    for fl in files:
        if fl.startswith(str(dt.isoweekday())):
            return fl
    return False


def update_next(days_delta):
    try:
        if not is_next_exist(days_delta):
            return False

        new_path = path_doc + path_to_term()

        if is_next_exist(days_delta):
            new_path += path_to_folders(days_delta)
        else:
            return False

        if is_next_exist(days_delta):
            new_path += path_to_files(days_delta)
        else:
            return False

        subprocess.call(['libreoffice6.1', '--convert-to', 'pdf', str(new_path)])  # convert docx to pdf
        # TODO fix version (e.g. libreoffice7.1) of libreoffice for LINUX
        # or swap 'libreoffice6.1' to 'YOUR_PATH\\LibreOffice\\program\\soffice.exe' for WINDOWS

        with Image(filename=(path_to_files(days_delta).split('.')[0] + '.pdf'), resolution=300) as img:  # pdf to jpg
            with img.convert('jpeg') as converted:
                converted.save(filename=(path_to_files(days_delta).split('.')[0] + '.jpg'))

        print("ready")
    except Exception as ex:
        print(ex)


def main():
    global today_hash
    global tomorrow_hash
    try:
        hashes = pickle.load(open("save.p", "rb"))  # load saved hashes from previous start
        today_hash = hashes["today_hash"]
        tomorrow_hash = hashes["tomorrow_hash"]

        refresh()
    except Exception as ex:
        print(ex)
    finally:
        gk = {"today_hash": today_hash, "tomorrow_hash": tomorrow_hash}
        pickle.dump(gk, open("save.p", "wb"))  # save new hashes


def is_next_exist(days_delta):
    if not path_to_files(days_delta):
        return False
    return True


def get_new_hash(is_today: bool):
    return hashlib.sha224(open(path_doc + path_to_term() + path_to_folders(next_day(is_today))
                               + path_to_files(next_day(is_today)), 'rb').read()).hexdigest()


def update_hash_and_notify_users(text_for_users: str, is_today: bool):
    update_next(next_day(is_today))

    print(text_for_users)
    write_to_all_users(text_for_users)
    return get_new_hash(is_today)


def refresh():
    global tomorrow_hash
    global today_hash

    subprocess.call([path_app + 'g.sh'])  # update drive
    # TODO delete for Windows

    if is_next_exist(next_day(True)):
        if today_hash == '':
            today_hash = update_hash_and_notify_users('Расписание на сегодня появилось', True)
            # send all from DB message about today schedule created

        elif today_hash != get_new_hash(True):
            today_hash = update_hash_and_notify_users('Расписание на сегодня изменилось', True)
            # send all from DB message about today schedule changed

    if is_next_exist(next_day(False)):
        print(is_next_exist(next_day(False)))
        if tomorrow_hash == '':
            tomorrow_hash = update_hash_and_notify_users('Расписание на завтра появилось', False)
            # send all from DB message about tomorrow schedule created

        elif tomorrow_hash != get_new_hash(False):
            tomorrow_hash = update_hash_and_notify_users('Расписание на завтра изменилось', False)
            # send all from DB message about tomorrow schedule changed

    if datetime.datetime.now().hour == 23 and datetime.datetime.now().minute >= 50:  # deleting old files
        filelist = [f for f in os.listdir(path_app) if
                    f.endswith(".jpg") and str(path_to_files(next_day(True)).split('.')[0]) in f]

        for f in filelist:
            os.remove(os.path.join(path_app, f))

        filelist = [f for f in os.listdir(path_app) if
                    f.endswith(".pdf") and str(path_to_files(next_day(True)).split('.')[0]) in f]

        for f in filelist:
            os.remove(os.path.join(path_app, f))

        today_hash = tomorrow_hash
        tomorrow_hash = ''


if __name__ == "__main__":
    main()
