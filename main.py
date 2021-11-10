import configparser
import os
import sqlite3
import zipfile
import base64

import bincopy as bc
import eel


i_path = 'iService/'

@eel.expose
def find_model(model):
    try:
        sqlite_connection = sqlite3.connect(i_path +'mdb.db')
        cursor = sqlite_connection.cursor()

        sqlite_select_query = (f"select  enumber from enumber_docs WHERE"
                               f" enumber like '{model}%' and docnum like '8%'"
                               f"LIMIT 10")
        record = [item[0] for item in cursor.execute(sqlite_select_query)]
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    except TypeError:
        print('Модель не найдена!')
    finally:
        if (sqlite_connection):
            sqlite_connection.close()

    return record


@eel.expose
def get_data(model):
    record = 0
    try:
        sqlite_connection = sqlite3.connect(i_path + 'mdb.db')
        cursor = sqlite_connection.cursor()

        sqlite_select_query = (f"select docnum from enumber_docs WHERE"
                               f" enumber like '{model}' and docnum like '8%'")
        cursor.execute(sqlite_select_query)
        record = str(cursor.fetchone()[0])
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    except TypeError:
        print('Модель не найдена!')
    finally:
        if (sqlite_connection):
            sqlite_connection.close()

    if not record:
        return 0

    filelist = os.listdir(i_path)
    file = ''
    for file in filelist:
        if record in file:
            break

    arc_path = i_path + file
    config = configparser.ConfigParser()
    
    with zipfile.ZipFile(arc_path, 'r') as zip1:
        for f_name in zip1.namelist():
            if f_name.lower() == 'z_cpu.ini':
                config_file = f_name
                break

        try:
            config.read_string(zip1.read('config_file').decode("utf-8"))
        except KeyError:
            return 0
        mcu = config['Controller']['Name']
        if 'STM32F1XX' == mcu:
            st = int('8000000', 16)
        elif 'R5F2136CA' == mcu:
            st = 0
        else:
            return 0

        file = bc.BinFile()
        file.add_srec(zip1.read('z_Software.s19').decode("utf-8"), overwrite=True)

    return base64.b64encode(file.as_binary(st)).decode('utf-8')


def check_db(path):
    result = 0
    try:
        sqlite_connection = sqlite3.connect(path)
        cursor = sqlite_connection.cursor()
        sqlite_select_query = 'SELECT count(name) FROM sqlite_master ' \
                              'WHERE type="table" AND name="enumber_docs"'
        cursor.execute(sqlite_select_query)
        result = cursor.fetchone()[0]
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if (sqlite_connection):
            sqlite_connection.close()

    return result

def make_db(i_path):
     result = 0
     if check_db(i_path + 'opec.sqlite'):
         try:
             sqlite_connection = sqlite3.connect(i_path + 'mdb.db')
             cursor = sqlite_connection.cursor()
             cursor.execute(f'ATTACH DATABASE \'{i_path + "opec.sqlite"}\' AS opec;')
             cursor.execute('CREATE TABLE enumber_docs AS SELECT * FROM opec.enumber_docs;')
             sqlite_connection.commit()
             result = 1
         except sqlite3.Error as error:
             print("Ошибка при подключении к sqlite", error)
         finally:
             if (sqlite_connection):
                 sqlite_connection.close()
     return result
if __name__ == '__main__':
    eel.init('www')
    if os.path.exists(i_path + 'opec.sqlite'):
        if os.path.exists(i_path + 'mdb.db'):
            eel.start('index.html', mode="chrome", size=(560, 460))
        else:
            if make_db(i_path):
                eel.start('index.html', mode="chrome", size=(560, 460))
            else:
                eel.start('error.html', mode="chrome", size=(560, 460))
    else:
        eel.start('error.html', mode="chrome", size=(560, 460))


