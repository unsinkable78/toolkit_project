from pandas import set_option, read_csv, ExcelFile
from xlsxwriter import Workbook
import logging
import time
import re
import modules.AddressParser as AddressParser
import pylev
import os

class Permsearch():
    def __init__(self, progress_text) -> None:
        self.start = time.time()
        self.progress_text = progress_text
        self.err = []
        self.reerr = []
    
        self.nameInList = []
        self.nameStatList = []
        self.addressList = []
        self.address1Splited = []
        self.address2Splited = []
        self.perm = []
        
        self.outList = []
        self.dictsFiltred = [[] for _ in range(6)]
        self.dictsParsed = []

    def files_initialization(self, stat:str, file:str) -> None:
        # Инициализация файлов
        self.progress_text.config(text='Инициализация файлов...')
        print('Инициализация файлов...')
        try:
            logging.getLogger().setLevel(logging.ERROR)

            set_option('display.max_rows', None)
            set_option('display.max_columns', None)
            set_option('display.max_colwidth', None)

            file
            stat
            self.dicts = 'dict.csv'

            current_directory = os.getcwd()
            output_folder_path = os.path.join(current_directory, "output")
            output_file = os.path.join(output_folder_path, "permsearch_result.xlsx")
            print(output_file)
            self.out = Workbook(output_file)
            self.sheet = self.out.add_worksheet()        

            self.sheet.write_string(0, 0, 'Название')
            self.sheet.write_string(0, 1, 'Адрес')
            self.sheet.write_string(0, 2, 'Пермалинк')
            self.sheet.write_string(0, 3, 'Результат')
            self.sheet.write_string(0, 4, 'Совп. осн.')
            self.sheet.write_string(0, 5, 'Совп. дом')
            self.sheet.write_string(0, 6, 'Уверенность, %')

            self.sheet.set_column(0, 0, 25)
            self.sheet.set_column(1, 1, 40)
            self.sheet.set_column(2, 3, 15)
            self.sheet.set_column(6, 6, 15)

            self.xl = ExcelFile(file)
            self.xl2 = ExcelFile(stat)
            self.dictsParsed = read_csv(self.dicts)

            self.df = self.xl.parse('Sheet1')
            self.dfStat = self.xl2.parse('Информация')

        except:
            if 11 not in self.err:
                print('Ошибка инициализации файлов')
                self.err.append(11)

    def load_dicts(self):
            # Загрузить словари из dicts.csv
            self.progress_text.config(text='Загрузка словарей...')
            print('Загрузка словарей...')
            try:
                pattern = re.compile(r'[а-яА-ЯёЁ\-/()№]+')

                self.dictsFiltred[0] = self.dictsParsed['bannedWords'].dropna().apply(lambda x: ' '.join(pattern.findall(str(x))).strip()).tolist()
                self.dictsFiltred[1] = self.dictsParsed['totallyBannedWords'].dropna().apply(lambda x: ' '.join(pattern.findall(str(x))).strip()).tolist()
                self.dictsFiltred[2] = self.dictsParsed['streetPointers'].dropna().apply(lambda x: ' '.join(pattern.findall(str(x))).strip()).tolist()
                self.dictsFiltred[3] = self.dictsParsed['housePointers'].dropna().apply(lambda x: ' '.join(pattern.findall(str(x))).strip()).tolist()
                self.dictsFiltred[4] = self.dictsParsed['indoorPointers'].dropna().apply(lambda x: ' '.join(pattern.findall(str(x))).strip()).tolist()
                self.dictsFiltred[5] = self.dictsParsed['nonHouseMarkers'].dropna().apply(lambda x: ' '.join(pattern.findall(str(x))).strip()).tolist()

                for i in range(len(self.dictsFiltred)):
                    if i < len(self.dictsFiltred):
                        self.dictsFiltred[i] = [word for word in self.dictsFiltred[i] if word]
            except:
                if 1 not in self.err:
                        self.err.append(1)

    def parse_addresses(self):   
        # Получить из адресов "основную часть" и номер дома
        self.progress_text.config(text='Парсинг адресов...')
        print('Парсинг адресов...')
        if 11 not in self.err:
            for i in range(len(self.df)):
                try:
                    self.addressList.append(self.df.at[i, 'Адрес'])
                    self.address1Splited.append(AddressParser.Parse(self.df.at[i, 'Адрес'], self.dictsFiltred))
                    self.nameInList.append(self.df.at[i, 'Название'])
                except:
                    print('Ошибка парсинга адреса: ', self.df.at[i, 'Адрес'])
                    if 2 not in self.err:
                        self.err.append(2)
            
            for i in range(len(self.dfStat)):
                try:
                    self.address2Splited.append(AddressParser.Parse(self.dfStat.at[i, 'Адрес'], self.dictsFiltred))
                    self.perm.append(self.dfStat.at[i, 'Пермалинк'])
                    self.nameStatList.append(self.dfStat.at[i, 'Название'])
                except:
                    print('Ошибка парсинга адреса: ', self.dfStat.at[i, 'Адрес'])
                    if 3 not in self.err:
                        self.err.append(3)

    def start_searching(self, progress, res_text_list):
        # Начать поиск пермалинков
        if self.err == []:
            self.progress_text.config(text='Поиск...')
            print('Поиск...')
            
            self.outList, self.reerr = self.permsearch(self.address1Splited, self.address2Splited, self.nameInList, self.nameStatList, self.addressList, progress, res_text_list)

            for code in self.reerr:
                self.err.append(code)

    def permsearch(self, address1Splited, address2Splited, nameInList, nameStatList, addressList, progress, res_text_list):  

        totalOKs = 0 
        uniqOKs = 0
        outList = []    
        upperPrec = 51
        i = 0

        for address1 in address1Splited:
                
            method = 2
            prec = upperPrec    

            compareMainResults = []
            compareBuildNumResults = []    
            
            reerr = []
            percLvl:float = 0      
            permsOut:int = 0
            ratingMain:float = -1
            ratingBlock:float = -1        
            foundedIndex:int = 0
            tempPrec:float = 0

            name = ''
            
            index = 0

            while permsOut == 0 and method >= 0:
                index = 0
                for address2 in address2Splited:

                    namesCompRes = 0              
                    index += 1

                    try:
                        namesCompRes = self.names_comparison(str(nameInList[i]), str(nameStatList[index - 1]))
                    except:
                        print('Ошибка при сравнении названий')
                        if 4 not in reerr:
                            reerr.append(4)
                    
                    if namesCompRes >= 0.2:
                        try:
                            compareMainResults = self.main_parts_comparison(address1[0], address2[0], prec)
                        except:
                            print('Ошибка при сравнении основных частей адреса')
                            if 5 not in reerr:
                                reerr.append(5)
                        if compareMainResults[0] == 0:                      
                            continue   
                        try:
                            compareBuildNumResults = self.compare_building_number(address1[1], address2[1], method)
                        except:
                            print('Ошибка при сравнении номеров дома')
                            if 6 not in reerr:
                                reerr.append(6)
                    else:
                        continue

                    if method >= 1:
                        match = compareMainResults[0] * compareBuildNumResults[0]
                    if method < 1:
                        match = compareMainResults[0]                    

                    try:
                        if abs(compareMainResults[1] - 3) != 0:
                            tempPrec = ((compareMainResults[1]*2 + compareBuildNumResults[1]*0.5) / abs(compareMainResults[1] - 3) + compareMainResults[1] * 2) * namesCompRes
                        else:
                            tempPrec = ((compareMainResults[1]*2 + compareBuildNumResults[1]*0.5) * 4 + compareMainResults[1] * 2) * namesCompRes

                        if match == 1:
                            if percLvl <= tempPrec and self.perm:
                                ratingMain = compareMainResults[1]
                                ratingBlock = compareBuildNumResults[1]
                                permsOut = self.perm[index - 1]                            
                                percLvl = tempPrec
                                foundedIndex = index - 1
                    except:
                        print('Ошибка при поиске лучшего пермалинка')
                        if 7 not in reerr:
                            reerr.append(7)

                if percLvl > 4:
                    break
                
                method -= 1

            try:
                normRating = round((percLvl / 36 * 100) * ((ratingMain + 1) / 4) * ((ratingBlock + 1) / 4), 1)
            except:
                print('Ошибка при расчёте приведённого рейтинга')
                if 8 not in reerr:
                            reerr.append(8)

            try:
                if nameStatList and foundedIndex < len(nameStatList):
                    name = nameStatList[foundedIndex]
                else:
                    if i < len(nameInList):
                        name = nameInList[i]
                
                if percLvl >= 9 and ratingMain >= 2 and ratingBlock > 0:
                    uniqOKs += 1
                    totalOKs += 1
                    address2Splited.pop(foundedIndex)
                    self.perm.pop(foundedIndex)
                    nameStatList.pop(foundedIndex)
                else:
                    totalOKs += 1 

                toWrite = [name, addressList[i], permsOut, round(percLvl, 1), round(ratingMain, 1), round(ratingBlock, 1), normRating]        

                outList.append(toWrite)

                # print(name, address1, permsOut, round(percLvl, 1), round(ratingMain, 1), round(ratingBlock, 1), normRating)
            except:
                print('Ошибка при подготовке строки результата')
                if 9 not in reerr:
                    reerr.append(9) 

            i += 1
            if len(address1Splited) != 0:
                progress.set(i / len(address1Splited))
            else:
                progress.set(1)

        try:
            print('Надёжные результаты / Общее количество / Процент надёжных')
            print(uniqOKs, '/', len(address1Splited), '/', ''.join([str(round(uniqOKs/len(address1Splited) * 100)), '%']))
            res_text_list.append(str(uniqOKs) + ' / ' + str(len(address1Splited)) + ' / ' + ''.join([str(round(uniqOKs/len(address1Splited) * 100)), '%']))
        except:
            print('Ошибка при подсчёте результатов')
            if 10 not in reerr:
                        reerr.append(10)

        return outList, reerr

    def prepare_results(self, res_text_list):
        self.progress_text.config(text='Подготовка результатов...')
        print('Подготовка результатов...')

        self.set_formats()
        self.write_result(self.outList)

        self.xl.close()
        self.xl2.close()
        self.out.close()

        self.end = time.time() - self.start

        if self.err == []:
            self.progress_text.config(text='Задача завершена успешно!')
            print('Задача завершена успешно') 
            time_elapsed = 'Затраченное время: ' + str(round(self.end, 3)) + ' сек.'
            res_text_list.append(time_elapsed)
            print(time_elapsed)
        else:
            text_result = 'Во время выполнения обнаружена ошибка!'
            text_error_codes = 'Коды ошибок: ' + str(self.err)
            self.progress_text.config(text=text_result)
            res_text_list.append(text_error_codes)
            if len(self.err) == 1:
                print('Задача завершена с кодом ошибки', self.err)
            if len(self.err) > 1:
                print('Задача завершена с кодами ошибки', self.err)
            print('Во время выполнения обнаружена ошибка. Проверь код ошибки в файле "коды ошибок"')
        
        # input('Нажми ENTER для выхода из программы')

    def write_result(self, outList): 
        # Записать результат в файл   
        i = 1
        ratingList = ['НЕТ', 'РУЧНОЙ', 'НИЗКИЙ', 'ВЫСОКИЙ', 'НАДЁЖНЫЙ']
        for toWrite in outList:
            
            for j in range(7):
                    try:
                        if toWrite[3] >= 20 and toWrite[5] >= 1:
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format1)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[4]), self.format1)

                        if toWrite[3] >= 20 and int(toWrite[5]) < 1:
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format2)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[2]), self.format2)

                        if toWrite[3] >= 9 and toWrite[3] < 20 and toWrite[5] >= 1:
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format1)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[3]), self.format1)

                        if toWrite[3] >= 9 and toWrite[3] < 20 and int(toWrite[5]) < 1:
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format2)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[2]), self.format2)

                        if (toWrite[3] >= 5 and toWrite[3] < 9) or (toWrite[3] >= 9 and toWrite[3] < 20 and toWrite[5] < 2):
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format2)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[2]), self.format2)

                        if toWrite[3] > 0 and toWrite[3] < 5:
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format3)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[1]), self.format3)

                        if toWrite[3] <= 0:
                            if j != 3:
                                self.sheet.write_string(i, j, str(toWrite[j]), self.format3)
                            else:
                                self.sheet.write_string(i, j, str(ratingList[0]), self.format3)
                    except:
                        self.sheet.write_string(i, j, str(toWrite[j]))
            i += 1

    def set_formats(self):
        # Задать форматы вывода
        self.format1 = self.out.add_format({'bg_color':   '#b3ffb6'})
        self.format2 = self.out.add_format({'bg_color':   '#faff7a'})
        self.format3 = self.out.add_format({'bg_color':   '#ffb3b3'})
        self.format4 = self.out.add_format({'bg_color':   '#ffb900'})

    def compare_building_number(self, address1:str, address2:str, method):  
        # Сравнить номер дома
        match = 0

        if address1[0] != address2[0]:
            return [0, 0]
        
        if address1 == address2:
            return [1, 3.0]
        
        lastNonEmpty = 0
        nonEmptyCount = 0
        matchCount = 0

        for i in range(4, -1, -1):
            if (address1[i].strip() or address2[i].strip()) and lastNonEmpty == 0:
                lastNonEmpty = i
            if address1[i].strip() and address2[i].strip():
                nonEmptyCount += 1
        
        for i in range(5):
            if address1[i] == address2[i] and address1[i] != '' and address2[i] != '':
                match += 1
                matchCount += 1
            if address1[i] != '' and address2[i] == '' or address1[i] == '' and address2[i] != '':
                match -= 0.2
                matchCount += 1

        if nonEmptyCount != 0:
            match *= 3 / nonEmptyCount
        else:
            match = 0

        if match > 0:
            result = [1, match] 
        else: result = [0, match]

        return result

    def main_parts_comparison(self, address1:str, address2:str, prec):
        # Сравнить "основную часть"
        matches = 0  
        match = 0  

        for word in address1:
            if word in address2:
                matches += 1

        if  len(address1) != 0:
            if matches / len(address1) > 0.49:
                match = 1
            result = [match, matches / len(address1) * 3]
        else:
            match = 0
            result = [match, 0]

        return result

    def names_comparison(self, name1:str, name2:str):
        # Сравнить названия
        if name1 != 'nan':
            res = 1 - pylev.levenschtein(name1, name2) / (len(name1) + len(name2))
            if res >= 0.5:
                return res
            else:
                return 0
        else:
            return 1

def start_permsearch(files, progress, progress_text, res_text_list) -> list:
    print(files)
    stat = files[0][0]
    address = files[1][0]
    ps = Permsearch(progress_text)
    ps.files_initialization(stat, address)
    ps.load_dicts()
    ps.parse_addresses()
    ps.start_searching(progress, res_text_list)
    ps.prepare_results(res_text_list)
    return ps.err

# BUG баг-лист
# ==========================================================================================================
# 1) Лучшие результаты не перезаписывают старые (РЕШЕНО)
# Баг возникает из-за ошибке в логике выбора наилучшего результата.
# Сейчас выбирается результат, только если рейтинг дома И рейтинг основы меньше другого результата.
# В случае, если у адреса указан номер дома с ошибкой, алгоритм находит дом с большим рейтингом совпадений.
# Но их суммарный рейтинг может оказаться выше, даже если рейтинг сравнения основы у правильного адреса больше.
#
# Варианты решения:
#
# 1. Ввести новый рейтинг для сравнения с модификатором на разницу между рейтингом основы и рейтингом дома.
# 2. Ввести проверку на точное совпадение основы (не эффективно).
# 3. Изменить правила вычисления основного рейтинга. Точные совпадения дают больший вклад, неточные - меньший. Тогда требуется вводить новый
#    словарь в парсер для повышения степени "очистки" адреса от мусорных слов.
# 4. Переделать систему рейтинга, добавив в формулу расчёта дополнительные условия +
# ==========================================================================================================
# 2) Ошибка в определении лучшего результата, если совпадает город и номер дома (РЕШЕНО)
#
# Варианты решения:
# 1) Увеличить вес совпадения по основе и уменьшить вес номера дома в рейтинге сравнения (сейчас вклад одинаков)
# 2) Определять улицу и город и считать отдельно совпадения по ним (сложно, требует переписывания части кода парсера // точно определить улицу получится не во всех случаях)
# ==========================================================================================================

# TODO
# ==========================================================================================================
# - привести шкалу рейтинга совпадений основы к шкале рейтинга совпадений дома (СДЕЛАНО)
#   Сейчас:
#   шкала рейтинга основы - это количество совпавших слов в адресе
#   шкала рейтинга дома - 0-3
#   Сделать:
#   привести все шкалы к единой системе оценки рейтинга (например, 0-5)
# ==========================================================================================================
# - привести рейтинг в отчёте к 100-бальной шкале (СДЕЛАНО)
# ==========================================================================================================
# - изменить вывод уровня надёжности исходя из рейтинга сравнения или итоговой 100-бальной шкалы (СДЕЛАНО)
# ==========================================================================================================
# - проанализировать до конца файл отчёта по магниту и выявить все случаи ошибок/сомнений/неточностей (СДЕЛАНО)