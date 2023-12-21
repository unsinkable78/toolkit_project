import os
import sys
from pandas import ExcelFile
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from modules.class_analysis_base import analysis_base

def test_get_date_from_filename():
    a_b = analysis_base()
    result = a_b.get_date_from_filename('stat_Спортмастер_Month_2023-07-24_2023-10-29_58399379.xlsx')
    assert result == ['2023-07-24', '2023-10-29']

    a_b = analysis_base()
    result = a_b.get_date_from_filename('')
    assert result == []

    a_b = analysis_base()
    result = a_b.get_date_from_filename('aaaaaaaaaaaaaaaaaaa')
    assert result == []

def test_parse_date():
    a_b = analysis_base()
    result = a_b.parse_date(['2023-07-24', '2023-10-29'])
    assert result == [['2023', '07', '24'], ['2023', '10', '29']]

    a_b = analysis_base()
    result = a_b.parse_date(['1111-11-11'])
    assert result == [['1111', '11', '11']]

    a_b = analysis_base()
    result = a_b.parse_date(['aaaaaaaaaaa'])
    assert result == [['aaaaaaaaaaa']]

    a_b = analysis_base()
    result = a_b.parse_date([''])
    assert result == [['']]

def test_format_date_ddmmyyy():
    a_b = analysis_base()
    result = a_b.format_date_ddmmyyy('2023-10-29')
    assert result == '29.10.2023'

    a_b = analysis_base()
    result = a_b.format_date_ddmmyyy('aaaaaaaaaaaaaaaaaaaaaaaaaa')
    assert result == 'aaaaaaaaaaaaaaaaaaaaaaaaaa'

    a_b = analysis_base()
    result = a_b.format_date_ddmmyyy('')
    assert result == ''

def test_get_company_name():
    a_b = analysis_base()
    result = a_b.get_company_name('stat_Спортмастер_Month_2023-07-24_2023-10-29_58399379.xlsx')
    assert result == 'Спортмастер'

    a_b = analysis_base()
    result = a_b.get_company_name('stat_Спортмастер')
    assert result == '[УКАЖИ НАЗВАНИЕ КЛИЕНТА]'
    
    a_b = analysis_base()
    result = a_b.get_company_name('stat__Month')
    assert result == ''

    a_b = analysis_base()
    result = a_b.get_company_name('')
    assert result == '[УКАЖИ НАЗВАНИЕ КЛИЕНТА]'

def test_delta_date_calc():
    a_b = analysis_base()
    result = a_b.delta_date_calc([['2023', '07', '24'], ['2023', '10', '29']])
    assert result == 98

    a_b = analysis_base()
    result = a_b.delta_date_calc([['2000', '01', '00'], ['2001', '02', '00']])
    assert str(result) == 'day is out of range for month'

    a_b = analysis_base()
    result = a_b.delta_date_calc([['2000', '01', '01'], ['2000', '01', '01']])
    assert result == 1

    a_b = analysis_base()
    result = a_b.delta_date_calc([['2000', '00', '01'], ['2000', '00', '01']])
    assert str(result) == 'month must be in 1..12'

    a_b = analysis_base()
    result = a_b.delta_date_calc([[''], ['']])
    assert result == None

def test_parse_excel():
    a_b = analysis_base()
    curr_dir = os.getcwd()
    #tests_path = os.path.join(curr_dir, 'tests')
    file_path = os.path.join(curr_dir, 'test_excel_file.xlsx')
    result = a_b.parse_excel(file_path)
    assert len(result[0][0]) == 4
    assert "ТестА" in result[0][0]
    assert "ТестБ" in result[0][0]
    assert "ТестВ" in result[0][0]
    assert "ТестГ" in result[0][0]

def test_determine_campaign_type():
    a_b = analysis_base()
    curr_dir = os.getcwd()
    #tests_path = os.path.join(curr_dir, 'tests')
    file_path = os.path.join(curr_dir, 'this_is_like_priority.xlsx')
    excel_file_stat = ExcelFile(file_path)
    result = a_b.determine_campaign_type(excel_file_stat)
    assert result[0] == ['Лист1', 'Переходы в карточку', 'Ещё какой-то лист', 'Их точно больше двух', 'А в единой только 2 листа', 'Поэтому', 'Этот файл похож на приоритет']
    assert result[1] == 'priority'

    a_b = analysis_base()
    curr_dir = os.getcwd()
    #tests_path = os.path.join(curr_dir, 'tests')
    file_path = os.path.join(curr_dir, 'this_is_like_united.xlsx')
    excel_file_stat = ExcelFile(file_path)
    result = a_b.determine_campaign_type(excel_file_stat)
    assert result[0] == ['Лист1']
    assert result[1] == 'united'

def test_get_cols_names():
    a_b = analysis_base()
    curr_dir = os.getcwd()
    file_path = os.path.join(curr_dir, 'test_excel_file.xlsx')
    excel_file = ExcelFile(file_path)
    df = excel_file.parse()

    result = a_b.get_cols_names(df)
    assert result == ['ТестБ', 'ТестВ']

    result = a_b.get_cols_names(df, 0, 0)
    assert result == ['ТестА', 'ТестБ', 'ТестВ', 'ТестГ']

    result = a_b.get_cols_names(df, 1, 3)
    assert result == []

    result = a_b.get_cols_names(df, 1, 0)
    assert result == ['ТестБ', 'ТестВ', 'ТестГ']

    result = a_b.get_cols_names(df, 2, -2)
    assert result == ['ТестБ', 'ТестВ']

def test_get_rows_data():
    a_b = analysis_base()
    curr_dir = os.getcwd()
    #tests_path = os.path.join(curr_dir, 'tests')
    file_path = os.path.join(curr_dir, 'this_is_like_priority.xlsx')
    excel_file = ExcelFile(file_path)
    df = excel_file.parse()

    result = a_b.get_rows_data(df, 'priority', 0, 1)
    #assert result == [['Столбец A'], ['Строка 1'], ['Строка 2']]

    result = a_b.get_rows_data(df, 'priority', -1, 222)
    #assert result == [['Столбец A'], ['Строка 1'], ['Строка 2'], ['Строка 3']]

    result = a_b.get_rows_data(df, 'priority', -1, -1)
    #assert result == [['Столбец A']]

    file_path = os.path.join(curr_dir, 'this_is_like_united.xlsx')
    excel_file = ExcelFile(file_path)
    df = excel_file.parse()

    result = a_b.get_rows_data(df, 'united', 0, 1)
    assert result == [['Строка 1'], ['Строка 2']]

    result = a_b.get_rows_data(df, 'united', -1, 222)
    assert result == [['Строка 1'], ['Строка 2'], ['Строка 3']]

    result = a_b.get_rows_data(df, 'united', -1, -1)
    assert result == []