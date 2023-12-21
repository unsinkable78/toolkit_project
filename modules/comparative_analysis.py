from pandas import set_option
from xlsxwriter import Workbook
import logging
import os
from modules.class_analysis_base import analysis_base

class comparative_analysis(analysis_base):

    first_row = 0
    last_row = 15                                                   # Последняя строка, которая будет обрабатываться. По-умолчанию в стандартной стате -- это конец первой части сводной
    collapse = True
    all_data = False
    data_start = ''

    def __init__(self, filename_1:str, filename_2:str, collapse:bool, all_data:bool) -> None:
        # При инициализации экземпляра класса
        self.collapse = collapse
        self.all_data = all_data
        # Получить название клиента из названия файла
        company_name_from_file_1 = self.get_company_name(filename_1)
        company_name_from_file_2 = self.get_company_name(filename_2)
        if company_name_from_file_1 == company_name_from_file_2:
            self.company_name = company_name_from_file_1
        else:
            self.company_name = 'УКАЖИ НАЗВАНИЕ КЛИЕНТА'

        # Получить периоды сравнения из названия файла
        period_1 = super().get_date_from_filename(filename_1)
        period_2 = super().get_date_from_filename(filename_2)

        # Задать названия группы столбцов согласно периодам
        self.set_global_col_headers(period_1, period_2)

        # Распарсить дату из периодов
        period_1_parsed = super().parse_date(period_1)
        period_2_parsed = super().parse_date(period_2)

        # Вычислить количество дней в периоде, включая границы
        self.delta_days_period_1 = super().delta_date_calc(period_1_parsed)
        self.delta_days_period_2 = super().delta_date_calc(period_2_parsed)

        # Распарсить сводную таблицу в датафрейм
        self.df_stat_1_parsed, self.campaign_type = super().parse_excel(filename_1)
        self.df_stat_2_parsed, self.campaign_type = super().parse_excel(filename_2)

        if self.campaign_type == super().campaign_type_united:
            self.all_data = False

        self.first_row, self.last_row = super().get_data_borders(self.df_stat_1_parsed[1], self.campaign_type)

        # Получить названия cтрок из датафрейма в зависимости от того
        self.rows_data = super().get_rows_data(self.df_stat_1_parsed[1], self.campaign_type, self.first_row, self.last_row, all=self.all_data, collapse=self.collapse)
        

    def set_global_col_headers(self, period_1_str:str, period_2_str:str) -> None:
        # Сформировать строки, которые будут заголовком блока данных в сравнительном анализе
        self.head_pre_rc = 'Период до РК (%s – %s)' % (self.format_date_ddmmyyy(period_1_str[0]), self.format_date_ddmmyyy(period_1_str[1]))
        self.head_rc = 'Период c РК (%s – %s)' % (self.format_date_ddmmyyy(period_2_str[0]), self.format_date_ddmmyyy(period_2_str[1]))

    # region Формирование данных результата

    def fill_extra_rows(self, dataframe_1, dataframe_2, row_name:str, index) -> None:        
        if self.campaign_type == super().campaign_type_priority:
            disc_row_1 = self.find_row(dataframe_1, 'Адрес', row_name)
            disc_row_2 = self.find_row(dataframe_2, 'Адрес', row_name)
            start = 4
            result = [row_name]
            temp = []
            cols_num = super().get_cols_number(dataframe_1, 1) - 8
            for j in range(start, start + cols_num):
                if 4 <= j < cols_num + 8:
                    temp.append(dataframe_1.iloc[disc_row_1, j])
            result.extend(temp)
            result.append(round(sum(temp) / self.delta_days_period_1 * 30, 4))
            temp = []
            cols_num = super().get_cols_number(dataframe_2, 1) - 8
            for j in range(start, start + cols_num):
                if 4 <= j < cols_num + 8:
                    temp.append(dataframe_2.iloc[disc_row_2, j])
            result.extend(temp)
            result.append(round(sum(temp) / self.delta_days_period_2 * 30, 4))
            self.rows_data.insert(index, result)

    def fill_average_month(self, dataframe, delta_days:int) -> None:
        cols_num = 0
        if self.campaign_type == super().campaign_type_priority:
            cols_num = super().get_cols_number(dataframe)
        if self.campaign_type == super().campaign_type_united:
            cols_num = super().get_cols_number(dataframe) - 1
        start = len(self.rows_data[1]) - cols_num
        for i in range(len(self.rows_data)):
            if super().check_row(i, self.rows_data, cols_num):
                self.rows_data = super().fill_headers(i, self.rows_data, 'Среднее')
            else:
                temp_sum = 0
                for j in range(start, len(self.rows_data[i])):
                    temp_sum += self.rows_data[i][j]
                average = round(temp_sum / delta_days * 30, 4)
                self.rows_data = super().fill_processed_data(i, self.rows_data, average)

    def insert_row_into_rows_data(self, row:int, inserting_string) -> None:
        if inserting_string == '':
            inserting_string = ['']
        self.rows_data.insert(row, inserting_string)

    def find_average_pos(self) -> list:
        indicies = []
        for index, item in enumerate(self.rows_data[0]):
            if item == 'Среднее':
                indicies.append(index)
        return indicies

    def fill_groth(self):
        indicies = self.find_average_pos()
        if len(indicies) == 2:
            for i in range(len(self.rows_data)):   
                cols_num = len(self.rows_data[i]) - 1         
                if super().check_row(i, self.rows_data, cols_num):
                    self.rows_data = super().fill_headers(i, self.rows_data, header='Прирост, шт.')
                else:
                    groth = int(round(self.rows_data[i][indicies[1]] - self.rows_data[i][indicies[0]], 0))
                    self.rows_data = super().fill_processed_data(i, self.rows_data, groth)

    def fill_delta(self):
        indicies = self.find_average_pos()
        if len(indicies) == 2:
            for i in range(len(self.rows_data)):   
                cols_num = len(self.rows_data[i]) - 1         
                if super().check_row(i, self.rows_data, cols_num):
                    self.rows_data = super().fill_headers(i, self.rows_data, header='Дельта, %')
                else:
                    if self.rows_data[i][indicies[0]] != 0:
                        delta = self.rows_data[i][indicies[1]] / self.rows_data[i][indicies[0]] - 1
                    else:
                        delta = 1.0000
                    self.rows_data = super().fill_processed_data(i, self.rows_data, round(delta, 4))

    # endregion

    # region Вывод данных в файл

    def initialize_output_file(self) -> None:
        # Инициализировать файл для записи
        current_directory = os.getcwd()
        output_folder_path = os.path.join(current_directory, "output")
        file_name = '%s. Сравнительный анализ.xlsx' %(self.company_name)
        output_file = os.path.join(output_folder_path, file_name)
        self.out = Workbook(output_file)
        self.sheet = self.out.add_worksheet('Сравнительный анализ')

    def set_formats(self) -> None:
        # Задать форматы
        self.format_date_string_pre_rc = self.out.add_format({'bold':True, 'bg_color':'#DDEBF7', 'border':1, 'align':'center'})
        self.format_date_string_with_rc = self.out.add_format({'bold':True, 'bg_color':'#E2EFDA', 'border':1, 'align':'center'})

        self.format_main_cells_pre_rc = self.out.add_format({'bg_color':'#DDEBF7', 'border':1})
        self.format_main_cells_with_rc = self.out.add_format({'bg_color':'#E2EFDA', 'border':1})

        self.format_growth = self.out.add_format({'border':1})
        self.format_growth_less_zero = self.out.add_format({'font_color':'#9C0006', 'bg_color':'#FFC7CE','border':1})

        self.format_delta = self.out.add_format({'border':1, 'num_format':'0.00%'})
        self.format_delta_less_zero = self.out.add_format({'font_color':'#9C0006', 'bg_color':'#FFC7CE','border':1, 'num_format':'0.00%'})

        self.format_parameters_first = self.out.add_format({'bold':True, 'border':1, 'align':'center'})
        self.format_parameters_first_col1 = self.out.add_format({'bold':True, 'border':1})
        self.format_parameters = self.out.add_format({'border':1})
        self.format_parameters_extra = self.out.add_format({'border':1, 'italic':True, 'align':'right'})

        self.format_header_pre_rc = self.out.add_format({'bg_color':'#DDEBF7', 'border':1, 'align':'center'})
        self.format_header_rc = self.out.add_format({'bg_color':'#E2EFDA', 'border':1, 'align':'center'})

        self.format_default = self.out.add_format({'bg_color':'#FFFFFF', 'border':0})

    def set_standart_cell_lenght(self):
        # Задать ширину ячеек
        self.sheet.set_column(0, 0, 26)
        self.sheet.set_column(1, self.pre_rc_len + self.with_rc_len, 13)
        self.sheet.set_column(self.pre_rc_len + self.with_rc_len + 1, len(self.rows_data[1]) - 1, 14.29)

    def write_data(self) -> None:
        # Записать данные из rows_data
        self.initialize_output_file()
        self.set_formats()
        if self.campaign_type == super().campaign_type_priority:
            shift = 1
        if self.campaign_type == super().campaign_type_united:
            shift = 0
        self.pre_rc_len = super().get_cols_number(self.df_stat_1_parsed[1]) + shift
        self.with_rc_len = super().get_cols_number(self.df_stat_2_parsed[1]) + shift
        self.set_standart_cell_lenght()

        # region Записать заголовки в объединённые ячейки
        start_row = 0
        star_col = 1
        end_row = 0
        end_col = self.pre_rc_len
        self.sheet.merge_range(start_row, star_col, end_row, end_col, self.head_pre_rc, self.format_header_pre_rc)

        start_row = 0
        star_col = self.pre_rc_len + 1
        end_row = 0
        end_col = self.pre_rc_len + self.with_rc_len
        self.sheet.merge_range(start_row, star_col, end_row, end_col, self.head_rc, self.format_header_rc)

        self.sheet.write(0, end_col + 1, '', self.format_parameters)
        self.sheet.write(0, end_col + 2, '', self.format_parameters)
        # endregion

        last = len(self.rows_data[1]) - 1

        for i in range(len(self.rows_data)):
            for j in range(len(self.rows_data[i])):
                format = self.choose_format(i, j)
                if isinstance(self.rows_data[i][j], str):
                    self.sheet.write_string(i, j, self.rows_data[i][j], format)
                else:
                    if j == last:
                        self.sheet.write_number(i, j, self.rows_data[i][j], format)
                    else:                        
                        self.sheet.write_number(i, j, int(round(self.rows_data[i][j], 0)), format)

    def choose_format(self, i:int, j:int):
        # Метод выбора формата для конкретной ячейки (по координатам i j)
        chosen_format = ''
        if i == 1:
            if j == 0:
                chosen_format = self.format_parameters_first_col1
            elif 1 <= j <= self.pre_rc_len:
                chosen_format = self.format_date_string_pre_rc
            elif self.pre_rc_len < j <= self.pre_rc_len + self.with_rc_len:
                chosen_format = self.format_date_string_with_rc
            else:
                chosen_format = self.format_parameters_first
        elif self.rows_data[i][j] == 'дискавери' or self.rows_data[i][j] == 'прямые':
            chosen_format = self.format_parameters_extra
        else:
            if j == 0:
                chosen_format = self.format_parameters
            elif 1 <= j <= self.pre_rc_len:
                chosen_format = self.format_main_cells_pre_rc
            elif self.pre_rc_len < j <= self.pre_rc_len + self.with_rc_len:
                chosen_format = self.format_main_cells_with_rc
            elif j == len(self.rows_data[1]) - 1:
                if isinstance(self.rows_data[i][j], float):
                    if self.rows_data[i][j] >= 0:
                        chosen_format = self.format_delta
                    else:
                        chosen_format = self.format_delta_less_zero
                else:
                    chosen_format = self.format_parameters
            else:
                if isinstance(self.rows_data[i][j], int):    
                    if self.rows_data[i][j] >= 0:
                        chosen_format = self.format_growth
                    else:
                        chosen_format = self.format_growth_less_zero
                else:
                    chosen_format = self.format_parameters

        if i != 0 and self.is_row_empty(self.rows_data[i]):
            chosen_format = self.format_default

        if self.is_row_has_no_data(self.rows_data[i]):
            if j == 0:
                chosen_format = self.format_parameters_first_col1
            elif 1 <= j <= self.pre_rc_len:
                chosen_format = self.format_date_string_pre_rc
            elif self.pre_rc_len < j <= self.pre_rc_len + self.with_rc_len:
                chosen_format = self.format_date_string_with_rc
            else:
                chosen_format = self.format_parameters_first

        return chosen_format

    def close_file(self):
        self.out.close()

    # endregion

def make_comparative_analysis(stat:list, collapse, all_data, inverse) -> list:
    logging.getLogger().setLevel(logging.ERROR)
    set_option('display.max_rows', None)

    error = []
    stat.sort()

    if len(stat) == 2:
        ca = comparative_analysis(stat[0], stat[1], collapse, all_data)

        ca.rows_data = ca.fill_raw_data(ca.df_stat_1_parsed[1], ca.rows_data, ca.campaign_type)  
        ca.rows_data = ca.replace_empty_elements(ca.rows_data)            
        ca.fill_average_month(ca.df_stat_1_parsed[1], ca.delta_days_period_1)        
        ca.rows_data = ca.fill_raw_data(ca.df_stat_2_parsed[1], ca.rows_data, ca.campaign_type) 
        ca.rows_data = ca.replace_empty_elements(ca.rows_data) 
        ca.fill_average_month(ca.df_stat_2_parsed[1], ca.delta_days_period_2)        

        if ca.collapse == True and ca.campaign_type == ca.campaign_type_priority:
            ca.insert_row_into_rows_data(ca.find_row_in_list(ca.rows_data, ca.calls_mob_prior), ca.collapse_calls(ca.rows_data))
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.calls_mob_prior))
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.calls_web_prior))

        if ca.collapse == True and ca.campaign_type == ca.campaign_type_united:
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.calls_mob_united))
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.calls_web_united))

        if ca.collapse == True:
            collapsed_visits = ca.collapse_visits(ca.rows_data)
            visits_index = ca.find_row_in_list(ca.rows_data, ca.site_visits)            
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.site_visits))
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.action_button))
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.promotion))
            ca.rows_data.pop(ca.find_row_in_list(ca.rows_data, ca.showcase))
            ca.insert_row_into_rows_data(visits_index, collapsed_visits)
        
        if ca.campaign_type == ca.campaign_type_priority:
            ca.fill_extra_rows(ca.df_stat_1_parsed[3], ca.df_stat_2_parsed[3], ca.extra_row_discovery, 3)
            ca.fill_extra_rows(ca.df_stat_1_parsed[3], ca.df_stat_2_parsed[3], ca.extra_row_straight, 4)        

        ca.fill_groth()
        ca.fill_delta()

        if ca.campaign_type == ca.campaign_type_united:
            ca.rows_data[0][0] = ''
        ca.insert_row_into_rows_data(0, '')

        ca.write_data()
        ca.close_file()

        # for item in ca.rows_data:
        #     print(item)
    else:
        print('Ошибка! Для сравнительного анализа требуется 2 файла статистики!')

    return error
    
    