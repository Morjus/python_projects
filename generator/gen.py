#!/usr/bin/env python3
#v_0_0_3

import csv
from jinja2 import Environment, FileSystemLoader
import yaml
import re
import xlrd
import os
import fileinput
import sys
import shutil
from ipaddress import ip_address
from datetime import datetime
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

models = {
    '1':'HUAWEI S5320-28P-LI-AC',
    '2':'TP-Link T2600G'
    }

items = [] #Для списка с IP
full_yaml_file = [] #Для финального файла с yaml данными
legend = {
'а':'a',
'б':'b',
'в':'v',
'г':'g',
'д':'d',
'е':'e',
'ё':'yo',
'ж':'zh',
'з':'z',
'и':'i',
'й':'y',
'к':'k',
'л':'l',
'м':'m',
'н':'n',
'о':'o',
'п':'p',
'р':'r',
'с':'s',
'т':'t',
'у':'u',
'ф':'f',
'х':'h',
'ц':'ts',
'ч':'ch',
'ш':'sh',
'щ':'shch',
'ъ':'y',
'ы':'y',
'ь':"",
'э':'e',
'ю':'yu',
'я':'ya',

'А':'A',
'Б':'B',
'В':'V',
'Г':'G',
'Д':'D',
'Е':'E',
'Ё':'YO',
'Ж':'ZH',
'З':'Z',
'И':'I',
'Й':'Y',
'К':'K',
'Л':'L',
'М':'M',
'Н':'N',
'О':'O',
'П':'P',
'Р':'R',
'С':'S',
'Т':'T',
'У':'U',
'Ф':'F',
'Х':'H',
'Ц':'TS',
'Ч':'CH',
'Ш':'SH',
'Щ':'SHCH',
'Ъ':'Y',
'Ы':'Y',
'Ь':"",
'Э':'E',
'Ю':'YU',
'Я':'YA',
}

def latinizator(letter, dic):
    """Замена кириллицы в тексте на латиницу."""

    for i, j in dic.items():
        letter = letter.replace(i, j)
    return letter

def check_ip(ip):
    """Проверка корректности написанного IP-адреса. """

    try:
        ip_address(ip)
    except ValueError:
        return False
    else:
        return True

def transliterator(file):
    """Транслитерирует файл, раскладывает файл в список, собирает через _"""

    with fileinput.FileInput(file, inplace=True, backup='.bak') as f:
        for line in f:
            line = line.upper()
            name_list = line.split(' ')
            line = '_'.join(name_list)
            print(latinizator(line, legend), end='')

def csv_from_excel(table):
    """Converting xls,xlsx file to csv file."""
    
    wb = xlrd.open_workbook(table)
    sh = wb.sheet_by_index(0)
    result = script_files_path + 'result.csv'
    with open(result, 'w') as res:
        wr = csv.writer(res, lineterminator = '\r', quoting=csv.QUOTE_ALL)
        for rownum in range(sh.nrows):
            wr.writerow(sh.row_values(rownum))
    
    return result

def convert_switch_data_to_dict(line):
    """Список списков с данными превращает в словарь
    Затем сохраняет его в виде yaml, где название файла его ip."""

    list_line = []
    list_line = line[3].split('-')
    ranger = list(range(int(list_line[0]),int(list_line[1])+1))
    ports = list(range(1,25))
    acc_dict = dict(zip(ports,ranger))
    gateway_list = line[2].split('.')
    gateway = gateway_list[0] + '.' + gateway_list[1] + '.' + gateway_list[2] + '.1'
    
    item = {
        'HOSTNAME': line[0],
        'STP': int(line[1]),
        'IP': line[2],
        'GATEWAY': gateway,
        'MGMT': int(line[4]),
        'access_ports': acc_dict,
        'B2B_VLAN': int(str(line[4][0])+'00')
    }
    full_yaml_file.append(item)
    items.append(item['IP'])
    yaml_data_path = script_files_path + 'full_yaml'
    with open(yaml_data_path, 'w') as final:
        final.write(yaml.dump(full_yaml_file, default_flow_style=False, allow_unicode=True))
    return items #Возвращает список IP адресов, которые есть в изначальной таблице.

def converter(file):
    """Конвертирует ФАЙЛ CSV в YAML."""

    with open(file, 'r') as source: #, open(out_file, 'w') as res
        reader = csv.reader(source)
        next(reader)
        s = list(reader)
        for switch_data in s:
            list_of_ip = convert_switch_data_to_dict(switch_data)
    return list_of_ip    

def config_maker(ip):
    """Принимает на вход IP-адрес (причем yaml файл для конфигурации уже должен существовать),
     добавляет к этому IP .yaml, а затем генерирует конфиг"""

    yaml_data_path = script_files_path + 'full_yaml'
    if check_ip(ip):
        #try:
        if model == 'HUAWEI S5320-28P-LI-AC': #huawei
            env = Environment(loader = FileSystemLoader('TEMPLATES\\HUAWEI S5320-28P-LI-AC'))
            if b2b == '2':
                template = env.get_template('template_uno.txt')
            else:
                template = env.get_template('template.txt')
        elif model == 'TP-Link T2600G': #tp-link
            env = Environment(loader = FileSystemLoader('TEMPLATES\\TP-Link_T2600G'))
            template = env.get_template('template.txt')
        with open(yaml_data_path) as full:
            switches = yaml.safe_load(full)
        for switch in switches:
            config_name = switch['IP'] + '.cfg'
            address = switch['HOSTNAME']
            address = re.findall(r'([a-zA-Z]+\_+\d+|[a-zA-Z]+\_[a-zA-Z]+\_+\d+)', address)
            address = address[0]
            new_path = dir_maker(address,model)
            config_path = new_path + '\\' + config_name

            with open(config_path, 'w') as f:
                f.write(template.render(switch))
        #except:
        #   print('IP-address error. Please check your xls table for correct values of IPs.')

def model_choicer(model):
    if model == '1':
        return 'HUAWEI S5320-28P-LI-AC'
    elif model == '2':
        return 'TP-Link T2600G'
    else:
        print('Unknown model.')

def dir_maker(address,model):
    """Создаёт директории адресам, а затем по моделям коммутаторов. """

    current_dir = os.getcwd() #Адрес текущей директории 
    path_for_address = '\\' + address
    path_for_model = '\\' + model
    result = '\\RESULT'
    path = current_dir + result + path_for_address + path_for_model
    try:
        os.makedirs(path)
    except:
        pass
    finally:
        return path

def script_files():
    """Создаёт папку для файлов, которые генерятся в процессе работы скрипта. Затем они удаляются. """

    current_dir = os.getcwd()
    path_for_res = current_dir + '\\script_files'
    try:
        os.makedirs(path_for_res)
    except:
        pass
    return path_for_res

def input_maker():
    """Обрабатывает ввод команд на предмет корректности. Проверяет существование файла, проверяет корректный выбор коммутатора. """
    pass

if __name__ == '__main__':
    table_of_switches = input('Enter filename: ')
    b2b = str(input('For common enter 1\nFor b2b enter 2\nEnter:'))

    #table_of_switches = 'nov.xls'
    for k,v in models.items():
        print(f'To make {v} configuration enter {k}')
    switch_model = input("Enter: ")
    script_files_path = script_files() + '\\'

    model = model_choicer(str(switch_model))
    csv_file_path = csv_from_excel(table_of_switches)
    transliterator(csv_file_path)
    ip_list = converter(csv_file_path)

    pool = ThreadPool(2)
    pool.map(config_maker, ip_list)
    pool.close()
    pool.join()
    shutil.rmtree(script_files_path)
    input("Done. Press 'Enter' for exit." )
 