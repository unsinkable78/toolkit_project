from pandas import set_option, ExcelFile
from datetime import datetime
import re

class analysis_base:
    excluded_rows = {'Звонки (моб)', 'Просмотр телефона (веб)', 'Просмотры акции', 'Клики по витрине', 'Клики по кнопке действия'}
    campaign_type_priority = 'priority'
    campaign_type_united = 'united'

    extra_row_discovery = 'дискавери'
    extra_row_straight = 'прямые'

    calls_mob_prior = 'Звонки (моб)'
    calls_web_prior = 'Просмотр телефона (веб)'
    calls_mob_united = '    Звонки (моб)'
    calls_web_united = '    Просмотр телефона (веб)'
    site_visits = 'Переходы на сайт'
    action_button = 'Клики по кнопке действия'
    promotion = 'Просмотры акции'
    showcase = 'Клики по витрине'
        
    # region парсинг названия файла

    def get_date_from_filename(self, filename:str) -> list:
        # Получить все даты из названия файла в формате ГГГГ-ММ-ДД
        pattern = r'\d{4}-\d{2}-\d{2}'
        return re.findall(pattern, filename)

    def parse_date(self, period:list) -> list:
        # Преобразовать строки из списка с датами формата ГГГГ-ММ-ДД в список вида ['ГГГГ', 'ММ', 'ДД']
        return [list(date.split('-')) for date in period]
    
    def format_date_ddmmyyy(self, date:str) -> str:
        # Форматировать дату из ГГГГ-ММ-ДД в ДД.ММ.ГГГГ
        if len(date) >= 6:
            formated_date = date[-2:] + date[4:-2] + date[:4]
            return formated_date.replace('-', '.')
        else:
            return date
        
    def get_company_name(self, filename:str) -> str:
        # Метод ищет в стандартном названии файла подстроку с названием организации
        match = re.search(r'stat_(.*?)_Month', filename)
        if match:
            return match.group(1).replace('_', ' ')
        else:
            return '[УКАЖИ НАЗВАНИЕ КЛИЕНТА]'

    #endregion

    def delta_date_calc(self, period_parsed:list) -> int:
        # метод возвращает количество дней в распарсеном из названия файла периоде (включая границы)
        delta_days = 1
        try:
            if len(period_parsed) == 2:
                if len(period_parsed[0]) == 3 and len(period_parsed[1]) == 3:
                    delta_days = (datetime(int(period_parsed[1][0]), int(period_parsed[1][1]), int(period_parsed[1][2])) - datetime(int(period_parsed[0][0]), int(period_parsed[0][1]), int(period_parsed[0][2]))).days + 1
                    return delta_days
            return None
        except ValueError as err:
            return err
    
    # region парсинг листов статистики    

    def parse_excel(self, filename:str) -> tuple[list, str]:
        # Получить датафрейм из листа экселя и вернуть список с распарсенными листами и тик рк
        excel_file_stat = ExcelFile(filename)
        sheet_list, campaign_type = self.determine_campaign_type(excel_file_stat)
        df_stat_parsed = []
        for sheet in sheet_list:
            df_stat_parsed.append(excel_file_stat.parse(sheet).fillna(''))
        return df_stat_parsed, campaign_type
    
    def determine_campaign_type(self, excel_file:ExcelFile) -> str:
        # Определить тип рекламной кампании: приоритет или единая
        sheet_list = excel_file.sheet_names
        if len(sheet_list) > 2:
            return sheet_list, self.campaign_type_priority
        else:
            return sheet_list, self.campaign_type_united
    
    # endregion
    
    # region работа с датафреймами
    
    def get_cols_names(self, dataframe, start=1, end=1) -> list:
        # Получить список с названиями столбцов в указанном диапазоне
        # start -- начальный столбец диапазона (считается с 0)
        # end -- последний столбец диапазона (номер столбца с конца, 0 -- последний столбец)
        # По-умолчанию возвращаются названия столбцов без первого и последнего
        col_names = list(dataframe.columns)
        if  (0 <= start < len(col_names) - 1) and (0 <= len(col_names) - end - 1 < len(col_names)):
            return col_names[start:len(col_names)-end]
        else:
            if len(col_names) >= 3:
                return col_names[1:-1]
            else:
                return col_names
            
    def get_rows_data(self, dataframe, campaign_type:str, first_row=0, last_row=15, all=False, collapse=True) -> list:                        # Значение 15 соответствует концу первой части сводной таблицы, поэтому оно выбрано по-умолчанию
        # Получить названия строк из датафрейма
        # all = True -- получает все строки, False - только до last_row (по умолчанию -- конец первой части сводной)
        # collapse = True -- "схлопывать" показатели звонков и переходов на сайт     
        if all:
            first_row = 0
            last_row = len(dataframe)
        result = []
        if campaign_type == self.campaign_type_priority:
            result.append([self.get_cols_names(dataframe, 0)[0]])
        for i in range(first_row - 1, last_row + 1):
            if 0 <= i < len(dataframe):
                result.append([dataframe.iloc[i, 0]])
        return result
            
    def get_cols_number(self, dataframe, all=0) -> int:
        # По-умолчанию возвращает количество "полезных" столбцов датафрейма
        # all = 1 -- возвращаются все столбцы
        if all == 0 and dataframe.shape[1] >=3:
            return dataframe.shape[1] - 2
        else:
            return dataframe.shape[1]
        
    # endregion

    # region общие действия со статистикой
        
    def collapse_calls(self, rows_data:list) -> list:
        # Метод стандартным образом "схлопывает" показатели звонков
        index_calls = -1        
        for i in range(len(rows_data)):
            if 'Звонки (моб)' in rows_data[i] or '    Звонки (моб)' in rows_data[i]:
                index_calls = i
                break
        calls = ['Звонки']
        for j in range(1, len(rows_data[index_calls])):
            if 1 <= index_calls < len(rows_data) and 1 <= index_calls + 1 < len(rows_data):
                calls.append(rows_data[index_calls][j] + rows_data[index_calls + 1][j])
        return calls
    
    def collapse_visits(self, rows_data:list) -> list:
        # Метод стандартным образом "схлопывает" показатели переходов на сайт
        index_visits = -1        
        for i in range(len(rows_data)):
            if 'Переходы на сайт' in rows_data[i]:
                index_visits = i
                break
        visits = ['Переходы на сайт']
        for j in range(1, len(rows_data[index_visits])):
            if 1 <= index_visits < len(rows_data) and 1 <= index_visits + 1 < len(rows_data) and \
               1 <= index_visits + 2 < len(rows_data) and 1 <= index_visits + 3 < len(rows_data):
                visits.append(rows_data[index_visits][j] + rows_data[index_visits + 1][j] + rows_data[index_visits + 2][j] + rows_data[index_visits + 3][j])
        return visits
    
    def find_row_in_list(self, list:list, search_string:str) -> int:
        try:
            index = -1
            for i in range(len(list)):
                if search_string in list[i]:
                    index = i
                    break
            return index                
        except:
            return -1
    
    def get_dataframe_data(self, i:int, dataframe, campaign_type, first_col=1) -> list:
        # Метод копирует указанную строку i из датафрейма и добавляет её в список
        result = []
        col_nums = -1
        if campaign_type == self.campaign_type_priority:
            col_nums = self.get_cols_number(dataframe)
        if campaign_type == self.campaign_type_united:
            col_nums = self.get_cols_number(dataframe) - 1
        for j in range(first_col, col_nums + 1):
            if 0 <= j <= col_nums and 0 <= i < len(dataframe):
                result.append(dataframe.iloc[i, j])
        return result
    
    def fill_raw_data(self, dataframe, rows_data:list, campaign_type:str) -> list:
        # Метод заполняет список с данными значениями из датафрейма
        first_row, last_row = self.get_data_borders(dataframe, campaign_type)
        shift = first_row - 1                                                                      # настройка сдвига строк в датафрейме
        i = 0
        while i < len(rows_data):
            if 0 <= i < len(rows_data):
                if i == 0:
                    temp_row = self.get_cols_names(dataframe)
                    if campaign_type == self.campaign_type_priority:
                        rows_data[i].extend(temp_row)
                    if campaign_type == self.campaign_type_united:                        
                        rows_data[i].extend(temp_row[:-1])                    
                else:
                    rows_data[i].extend(self.get_dataframe_data(i + shift, dataframe, campaign_type))
                i += 1
            else:
                print('Ошибка при заполнении данных!')
                break
        return rows_data
    
    def find_first_row(self, dataframe) -> int:
        pass

    def fill_processed_data(self, i:int, rows_data:list, processed_data) -> list:        
        if 0 <= i < len(rows_data):
            rows_data[i].append(processed_data)
        return rows_data

    def fill_headers(self, i:int, rows_data:list, header='') -> list:
        if rows_data[i][0] != '':
                rows_data[i].append(header)
        else:
            rows_data[i].append('')
        return rows_data

    def check_row(self, i:int, rows_data:list, cols_num:int) -> bool:
        start = len(rows_data[i]) - cols_num
        skip_row = False
        for j in range(start, len(rows_data[i])):
            if 0 <= j < len(rows_data[i]):
                if isinstance(rows_data[i][j], str):
                    skip_row = True
                    break                    
        return skip_row
    
    def get_data_borders(self, dataframe, campaign_type:str) -> tuple[int, int]:
        first_row = -1
        last_row = -1
        if campaign_type == self.campaign_type_priority:
            first_row = self.find_row(dataframe, 'Всего', 'Показы в поиске')
            last_row = self.find_row(dataframe, 'Всего', 'Просмотры входов')            
        elif campaign_type == self.campaign_type_united:
            first_row = self.find_row(dataframe, 'Всего переходов', 'Открытия карточки', True)
            last_row = self.find_row(dataframe, 'Всего переходов', 'Просмотры входов', True)
        return first_row, last_row

    def find_row(self, dataframe, col_name:str, str:str, reverse=False) -> int:
        # Находит в датафрейме первую встреченную строку str в колонке col_name и возвращает номер этой строки
        # reverse=True -- изменяет порядок просмотра столбца (просмотр с конца)
        rows_count = dataframe.shape[0]
        disc_row = -1
        if reverse == False:
            for i in range(rows_count):
                if dataframe.at[i, col_name] == str:
                    disc_row = i
                    break
        else:
            for i in range(rows_count - 1, 0, -1):
                if dataframe.at[i, col_name] == str:
                    disc_row = i
                    break
        return disc_row
    
    def replace_empty_elements(self, rows_data:list) -> list:        
        result = [[] for _ in range(len(rows_data))]
        for i in range(len(rows_data)):  
            is_row_empty = self.is_row_empty(rows_data[i])
            if is_row_empty == False:
                for j in range(0, len(rows_data[i])):
                    if rows_data[i][j] != '':
                        result[i].append(rows_data[i][j])
                    else:
                        result[i].append(0)
            else:
                for j in range(0, len(rows_data[i])):
                    result[i].append('')
            
        return result
    
    def is_row_empty(self, row:list) -> bool:
        result = True
        for j in range(0, len(row)):
                if row[j] != '':
                    result = False
                    break
        return result
    
    def is_row_has_no_data(seld, row:list) -> bool:
        for item in row:
            if not isinstance(item, str):
                return False
        return True
        
    #endregion