from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from pathlib import Path
import os
import modules.interface as interface
import threading
import time

class MainMenuLine():
    def __init__(self) -> None:
        self.main_menu = Menu()

        self.configure_task_menu()        

        self.main_menu.add_cascade(label = "Задача", menu = self.task_menu)
        self.main_menu.add_cascade(label = "Настройки (WIP)")
        self.main_menu.add_cascade(label = "Справка (WIP)")

    def configure_task_menu(self):
        self.standard_stat_menu = Menu()
        self.standard_stat_menu.add_command(label = "Стандартная статистика (без POI) (WIP)", command = self.standard_stat)
        self.standard_stat_menu.add_command(label = "Стандартная статистика (c POI) (WIP)", command = self.standard_stat_poi)

        self.comparative_analysis_menu = Menu()
        self.comparative_analysis_menu.add_command(label = "Стандартный СА", command = self.comparative_analysis_standard)
        self.comparative_analysis_menu.add_command(label = "Стандартный СА с POI (WIP)", command = self.comparative_analysis_poi)
        self.comparative_analysis_menu.add_command(label = "СА в разбивке по филиалам (WIP)", command = self.comparative_analysis_by_address)

        self.task_menu = Menu()
        self.task_menu.add_cascade(label = "Стандартная статистика (WIP)", menu = self.standard_stat_menu)
        self.task_menu.add_cascade(label = "Сравнительный анализ", menu = self.comparative_analysis_menu)
        self.task_menu.add_command(label = "Статистика по конкурентам (WIP)", command = self.competitors_statistic)
        self.task_menu.add_command(label = "Поиск пермалинков", command = self.permsearch)
        self.task_menu.add_separator()
        self.task_menu.add_command(label = "Закрыть меню")

    def standard_stat(self):
        messagebox.showinfo("Cтатистика", text_work_in_progress)

    def standard_stat_poi(self):
        messagebox.showinfo("Cтатистика (с POI)", text_work_in_progress)

    def comparative_analysis_standard(self):
        new_window(interface.task_comparative_analysis_standard)

    def comparative_analysis_poi(self):
        messagebox.showinfo("Стандартный СА с POI", text_work_in_progress)

    def comparative_analysis_by_address(self):
        messagebox.showinfo("СА в разбивке по филиалам", text_work_in_progress)

    def competitors_statistic(self):
        messagebox.showinfo("Статистика по конкурентам", text_work_in_progress)

    def permsearch(self):
        new_window(interface.task_permsearch)

class App(Toplevel):

    def __init__(self) -> None:
        super().__init__()
        self.task_type = 'task'
        self.parameters = []        

        self.title(text_corpacc_toolkit)
        self.option_add("*tearOff", FALSE)
        window_width = 1000
        window_height = 700
        self.configure_window(self, window_width, window_height)
        self.menu = MainMenuLine()
        self.config(menu = self.menu.main_menu)
        self.resizable(False, False)

        self.filenames_base_gap_y = 0.06
        self.filenames_line_spacing = 0.04
        self.filenames_base_tabulation = 0.02

    def task(self, files, progress_var=None, progress_text=None):
        print('Task %s started' %(self.task_type))
        self.show_parameters(files)
        self.current_task = interface.task_start(self.task_type, files, self.parameters, progress_var, progress_text)
        if self.task_type != interface.task_permsearch:
            self.show_result()

    def configure_window(self, window, window_width, window_height) -> None:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def open_files(self, max_files_num:int, files:list, showed_files:list, offset_x=0.02, offset_y=0.06, filter_type='stat_'):
        filtred_files = self.filter_files(list(filedialog.askopenfilename(multiple=1)), filter_type)
        if len(files) < max_files_num and len(filtred_files) <= max_files_num - len(files):
            files.extend(filtred_files)
        else:
            messagebox.showinfo("Ошибка!", "Выбрано слишком много файлов!")
            return
        if not files:
            messagebox.showinfo("Ошибка!", "Файлов требуемого типа не найдено. Проверь правильность названий файлов.") 
            return
        self.show_file_names(files, showed_files, offset_x, offset_y)
        # print(self.files)

    def clear_files(self, files:list, showed_files:list, offset_y_base=0.06):
        self.offset_y = offset_y_base
        files.clear()
        for label in showed_files:
            label.destroy()
        showed_files.clear()     

    def show_file_names(self, filepaths:list, showed_files:list, offset_x=0, offset_y=0):
        files_parsed = self.parse_file_paths(filepaths)        
        for file in files_parsed:
            label_filename = ttk.Label(self, text=file, anchor='nw', font=(font_base, 10))
            label_filename.place(relx=self.label_file_base_pos_x + offset_x, rely=self.label_file_base_pos_y + offset_y)
            showed_files.append(label_filename)
            offset_y += self.filenames_line_spacing

    def filter_files(self, fileslist:list, filter_type:str) -> list:
        if filter_type == filter_type_stat:
            return [file for file in fileslist if filter_type_stat in file and filter_type_extension_xls in file]
        if filter_type == filter_type_extension_xls:
            return [file for file in fileslist if '.xls' in file]
        if filter_type == filter_type_no_filter:
            return [file for file in fileslist]

    def parse_file_paths(self, filepaths:list):
        return [Path(path).name for path in filepaths]
    
    def show_parameters(self, files):
        print(self.task_type)
        print(files)
        print(self.parameters)

    def show_result(self) -> None:
        # print(self.current_task.get_error_code())
        if not self.current_task.get_error_code():
            #messagebox.showinfo("Сравнительный анализ", "Задача завершена успешно! Результат находится в папке output.")
            window_result = WindowResult()
        else:
            error_codes = ', '.join([str(item) for item in self.current_task.get_error_code()])
            result = "Во время выполнения обнаружена ошибка! Коды ошибок: " + error_codes
            messagebox.showinfo("Ошибка!", result)

    def on_closing(self, files, files_showed):
        self.parameters.clear()
        self.clear_files(files, files_showed)
        self.destroy()
        main_app.deiconify()

class WIndowCompAnStandard(App):

    def __init__(self) -> None:
        super().__init__()
        self.task_type = interface.task_comparative_analysis_standard
        self.parameters = [False, False, False]
        self.files = []
        self.showed_files = []
        self.max_files_stat_num = 2
        self.collapse = BooleanVar()
        self.all_data = BooleanVar()
        self.inverse = BooleanVar()        

        self.label_file_base_pos_x = 0.07
        self.label_file_base_pos_y = 0.16

        self.configure_text()
        self.configure_buttons()
        self.configure_checkbox()

        self.protocol("WM_DELETE_WINDOW", lambda x = self.files, y = self.showed_files: self.on_closing(x, y))

    def set_main_app(self, m_a):
        self.main_app = m_a

    def on_checkbox_changed(self):
        self.parameters = [self.collapse.get(), self.all_data.get(), self.inverse.get()]
        # print(self.parameters)

    def configure_text(self):
        label_main = ttk.Label(self, text="Стандартный сравнительный анализ", anchor='n', font=(font_base, 20))
        label_main.place(relx=0.26, rely=0.06)       

        label_file = ttk.Label(self, text="Выбери файлы статистик", anchor='nw', font=(font_base, 14))
        label_file.place(relx=0.07, rely=0.16)

        label_instruction = ttk.Label(self, text="Инструкция:", anchor='center', font=(font_base, 14))
        label_instruction.place(relx=0.07, rely=0.58)
        label_instruction = ttk.Label(self, text="1. Выбери два файла со статистикой до РК и после.", anchor='center', font=(font_base, 12))
        label_instruction.place(relx=0.073, rely=0.64)
        label_instruction = ttk.Label(self, text="2. Задай нужные параметры в правой части окна.", anchor='center', font=(font_base, 12))
        label_instruction.place(relx=0.073, rely=0.68)
        label_instruction = ttk.Label(self, text="3. Нажми кнопку «Сравнить».", anchor='center', font=(font_base, 12))
        label_instruction.place(relx=0.073, rely=0.72)
        label_instruction = ttk.Label(self, text="Файлы перименовывать нельзя. Необходимо оставить стандартное название.", anchor='center', font=(font_base, 13))
        label_instruction.place(relx=0.07, rely=0.78)
        label_instruction = ttk.Label(self, text="Период сравнения определяется автоматически.", anchor='center', font=(font_base, 13))
        label_instruction.place(relx=0.07, rely=0.82)
        label_instruction = ttk.Label(self, text="В Единой подписке сравнительный анализ для всех показателей невозможен.", anchor='center', font=(font_base, 13))
        label_instruction.place(relx=0.07, rely=0.86)

    def configure_buttons(self):
        open_button = ttk.Button(self, text=text_open_file, command = lambda x = self.max_files_stat_num, y = self.files, z = self.showed_files: self.open_files(x, y, z))
        open_button.place(relx=0.31, rely=0.16)
        clear_button = ttk.Button(self, text=text_clear, command = lambda x = self.files, y = self.showed_files: self.clear_files(x, y))
        clear_button.place(relx=0.41, rely=0.16)

        open_button = MyButton(self, text="Сравнить", height=40, width=150, command = lambda x = self.files: self.task(x))
        open_button.place(relx=0.34, rely=0.47)
        open_button = MyButton(self, text="Другая аналитика", height=40, width=120, command = lambda x = self.files, y = self.showed_files: self.on_closing(x, y))
        open_button.place(relx=0.52, rely=0.47)

    def configure_checkbox(self):
        chkbtn_collapse = ttk.Checkbutton(self, text="Суммировать показатели «Звонки» и «Переходы на сайт»", variable=self.collapse, onvalue=1, offvalue=0, command=self.on_checkbox_changed)
        chkbtn_collapse.place(relx=0.58, rely=0.16)
        chkbtn_all_data = ttk.Checkbutton(self, text="Оставить разбивку по приложениям", variable=self.all_data, onvalue=True, offvalue=False, command=self.on_checkbox_changed)
        chkbtn_all_data.place(relx=0.58, rely=0.20)
        chckbtn_inverse = ttk.Checkbutton(self, text="Инвертировать периоды", variable=self.inverse, onvalue=True, offvalue=False, command=self.on_checkbox_changed)
        chckbtn_inverse.place(relx=0.58, rely=0.24)

class WindowPermsearch(App):

    def __init__(self) -> None:
        super().__init__()
        self.task_type = interface.task_permsearch
        self.file_stat = []
        self.showed_file_stat = []
        self.file_address = []
        self.showed_file_address = []
        self.max_files_stat_num = 1
        self.max_files_address_num = 1

        self.label_file_base_pos_x = 0.07
        self.label_file_base_pos_y = 0.16
        self.label_file_space_between = 0.15
        self.label_file_base_length = 0.31
        self.button_open_base_length = 0.1

        self.configure_text()
        self.configure_buttons()

        self.protocol("WM_DELETE_WINDOW", lambda x = self.file_stat, y = self.showed_file_stat, 
                                                z = self.file_address, a = self.showed_file_address: self.on_closing(x, y, z, a))

    def configure_text(self):
        label_main = ttk.Label(self, text="Поиск пермалинков по адресам", anchor='n', font=(font_base, 20))
        label_main.place(relx=0.26, rely=0.06)       

        label_file = ttk.Label(self, text="Выбери файл статистики", anchor='nw', font=(font_base, 14))
        label_file.place(relx=self.label_file_base_pos_x, rely=self.label_file_base_pos_y)

        label_file = ttk.Label(self, text="Выбери файл c адресами", anchor='nw', font=(font_base, 14))
        label_file.place(relx=self.label_file_base_pos_x, rely=self.label_file_base_pos_y + self.label_file_space_between)

        label_instruction = ttk.Label(self, text="Инструкция:", anchor='center', font=(font_base, 14))
        label_instruction.place(relx=0.07, rely=0.58)
        label_instruction = ttk.Label(self, text="1. Подготовь файлы с адресами и статистикой по знанию. Файлы должны быть формата .xls или .xlsx", anchor='center', font=(font_base, 12))
        label_instruction.place(relx=0.075, rely=0.64)
        label_instruction = ttk.Label(self, text="2. Выбери файл со скачанной из рекламного кабинета статистикой по всей сети..", anchor='center', font=(font_base, 12))
        label_instruction.place(relx=0.075, rely=0.68)
        label_instruction = ttk.Label(self, text="3. Выбери файл с адресами.", anchor='center', font=(font_base, 12))
        label_instruction.place(relx=0.075, rely=0.72)
        label_instruction = ttk.Label(self, text="4. Нажми кнопку «Начать поиск».", anchor='center', font=(font_base, 13))
        label_instruction.place(relx=0.075, rely=0.76)

    def configure_buttons(self):
        open_button_stat = ttk.Button(self, text=text_open_file, command = lambda x = self.max_files_stat_num, y = self.file_stat, z = self.showed_file_stat: self.open_files(x, y, z))
        open_button_stat.place(relx=self.label_file_base_length, rely=self.label_file_base_pos_y)

        clear_button_stat = ttk.Button(self, text=text_clear, command = lambda x = self.file_stat, y = self.showed_file_stat: self.clear_files(x, y))
        clear_button_stat.place(relx=self.label_file_base_length + self.button_open_base_length, rely=self.label_file_base_pos_y)

        open_button_address = ttk.Button(self, text=text_open_file, command = lambda x = self.max_files_stat_num, y = self.file_address, z = self.showed_file_address,
                                         a = self.filenames_base_tabulation, b = self.label_file_space_between + self.filenames_base_gap_y, c = filter_type_extension_xls: self.open_files(x, y, z, a, b, c))
        open_button_address.place(relx=self.label_file_base_length, rely=self.label_file_base_pos_y + self.label_file_space_between)

        clear_button_address = ttk.Button(self, text=text_clear, command = lambda x = self.file_address, y = self.showed_file_address: self.clear_files(x, y))
        clear_button_address.place(relx=self.label_file_base_length + self.button_open_base_length, rely=self.label_file_base_pos_y + self.label_file_space_between)

        task_start = MyButton(self, text="Начать поиск", height=40, width=150, command = lambda x = self.file_stat, y = self.file_address: self.task(x, y))
        task_start.place(relx=0.34, rely=0.47)
        
        task_another = MyButton(self, text="Другая аналитика", height=40, width=120, command = lambda x = self.file_stat, y = self.showed_file_stat, 
                                                z = self.file_address, a = self.showed_file_address: self.on_closing(x, y, z, a))
        task_another.place(relx=0.52, rely=0.47)

    def task(self, file_stat, file_address):
        files = [file_stat, file_address]
        self.progress_var = DoubleVar()
        self.window_progress = WindowProgress(self.progress_var, self)
        text_progress = self.window_progress.configure_text()
        super().task(files, self.progress_var, text_progress)
        self.start_waiting()
        self.withdraw()

    def on_closing(self, files:list, files_showed:list, file_address:list, files_address_showed:list):
        self.clear_files(file_address, files_address_showed)
        super().on_closing(files, files_showed)

    def start_waiting(self):
        thread_wait = threading.Thread(target=self.wait_for_complite)
        thread_wait.start()

    def wait_for_complite(self):
        a = self.progress_var.get()
        while a < 1 and not self.parameters:
            time.sleep(0.2)
            a = self.progress_var.get()
        #self.show_result()
        self.show_permsearch_info()
        self.btn_open_folder_enable()
        self.btn_interrupt_rename()

    def show_permsearch_info(self):
        shift_y = 0
        label = ttk.Label(self.window_progress, text="Сводка:", font=(font_base, 12))
        label.place(relx=0.06, rely=0.10 + shift_y)
        if self.progress_var.get() == 1:
            label = ttk.Label(self.window_progress, text="Надёжные / Всего адресов / Процент надёжных", font=(font_base, 10))
            label.place(relx=0.09, rely=0.18 + shift_y)
        for message in self.parameters:
            label = ttk.Label(self.window_progress, text=message, font=(font_base, 10))
            label.place(relx=0.09, rely=0.24 + shift_y)
            shift_y += 0.06      
    
    def btn_open_folder_enable(self):
        self.window_progress.button_open_folder.state(["!disabled"])

    def btn_interrupt_rename(self):
        self.window_progress.button_interrupt_text = "Закрыть"

class WindowResult(Toplevel):
    def __init__(self) -> None:
        super().__init__()
        self.title(text_corpacc_toolkit)
        window_width = 300
        window_height = 200
        self.configure_window(self, window_width, window_height)
        self.resizable(False, False)

        self.configure_text()
        self.configure_buttons()

    def configure_window(self, window, window_width, window_height) -> None:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def configure_text(self):
        label = ttk.Label(self, text=message_success, anchor='nw', font=(font_base, 12), wraplength=280)
        label.pack(padx=10, pady=30)

    def configure_buttons(self):
        button_open_folder = MyButton(self, text="Открыть папку", height=30, width=100, command=self.open_folder)
        button_open_folder.place(relx=0.15, rely=0.6)

        button_close = MyButton(self, text="Закрыть", height=30, width=90, command=self.on_closing)
        button_close.place(relx=0.53, rely=0.6)

    def open_folder(self):
        current_directory = os.getcwd()
        output_folder_path = os.path.join(current_directory, "output")
        print(output_folder_path)
        if os.name == 'posix':
            os.system(f'xdg-open "{output_folder_path}')
        elif os.name == 'nt':
            os.system(f'explorer "{output_folder_path}')
        else:
            messagebox.showinfo("Ошибка!", "Не могу определить тип операционной системы! Открой папку вручную.")
        self.destroy()

    def on_closing(self):
        self.destroy()

class WindowProgress(Toplevel):
    def __init__(self, progress, master) -> None:
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master = master
        self.progress_var = progress
        self.title(text_corpacc_toolkit)
        window_width = 400
        window_height = 300
        self.resizable(False, False)
        self.configure_window(self, window_width, window_height)
        self.configure_progressbar()
        self.configure_buttons()

    def configure_window(self, window, window_width, window_height) -> None:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def configure_progressbar(self):
        progressbar = ttk.Progressbar(self, variable=self.progress_var, maximum=1, length=350)
        progressbar.place(relx=0.06, rely=0.66)

    def configure_text(self):
        label = ttk.Label(self, text=text_progress, anchor='nw', font=(font_base, 12), wraplength=280)
        label.place(relx=0.06, rely=0.5)

        text_current_status = Label(self, text="", font=(font_base, 10))
        text_current_status.place(relx=0.09, rely=0.58)
        return text_current_status
    
    def configure_buttons(self):
        self.button_interrupt_text = "Не нажимать"

        self.button_open_folder = ttk.Button(self, text=text_open_folder, command=self.open_folder)
        self.button_open_folder.place(relx=0.23, rely=0.78)
        self.button_open_folder.state(["disabled"])

        self.button_task_interrupt = ttk.Button(self, text=self.button_interrupt_text)
        self.button_task_interrupt.place(relx=0.53, rely=0.78)

    def open_folder(self):
        current_directory = os.getcwd()
        output_folder_path = os.path.join(current_directory, "output")
        print(output_folder_path)
        if os.name == 'posix':
            os.system(f'xdg-open "{output_folder_path}')
        elif os.name == 'nt':
            os.system(f'explorer "{output_folder_path}')
        else:
            messagebox.showinfo("Ошибка!", "Не могу определить тип операционной системы! Открой папку вручную.")
        self.on_closing()

    def on_closing(self):
        self.master.destroy()
        window = WindowPermsearch()
        self.destroy()

class MyButton(ttk.Frame):
    def __init__(self, parent, text="Запуск задачи...", height=None, width=None, *args, **kwargs):
        ttk.Frame.__init__(self, parent, height=height, width=width)

        self.pack_propagate(0)
        self._btn = ttk.Button(self, text=text, *args, **kwargs)
        self._btn.pack(fill=BOTH, expand=1)

def new_window(window_type:str):    
        if window_type == interface.task_comparative_analysis_standard:
            window = WIndowCompAnStandard()
        if window_type == interface.task_permsearch:
            window = WindowPermsearch()
        main_app.withdraw()

def on_closing_root(root):
    root.destroy()

def main_app_settings(main_app, root):
    label_main_corp = ttk.Label(main_app, text=text_corpacc_toolkit, anchor='n', font=(font_base, 20))
    label_main_corp.pack(anchor='n', pady=50)
    label_main_wip = ttk.Label(main_app, text=text_work_in_progress, anchor='n', font=(font_base, 18))
    label_main_wip.pack(anchor='n', pady=200)
    main_app.protocol("WM_DELETE_WINDOW", lambda x = root: on_closing_root(x))

message_success = 'Задача выполнена успешно! Результат помещён в папку output.'
text_corpacc_toolkit = "CORPACC Analytic Toolkit"
text_work_in_progress = "Work in Progress"
text_open_folder = "Показать в папке"
text_progress = "Прогресс:"
text_open_file = "Открыть файл"
text_clear = "Очистить"
font_base = "Arial"

filter_type_stat = 'stat_'
filter_type_unload = ''
filter_type_extension_xls = '.xls'
filter_type_no_filter = ''

root = Tk()
main_app = App()
main_app_settings(main_app, root)
root.withdraw()
root.mainloop()

