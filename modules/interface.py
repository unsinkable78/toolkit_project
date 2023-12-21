import modules.comparative_analysis as comparative_analysis
import modules.Permsearch as Permsearch
import threading

task_comparative_analysis_standard = 'task_ca_st'
task_permsearch = 'task_permsearch'

class task_start:

    def __init__(self, task_type:str, files:list, parameters:list, progress_var=None, progress_text=None) -> int:
        self.task_type = task_type
        self.files = files
        self.parameters = parameters
        self.error = []
        self.progress = progress_var
        self.progress_text = progress_text

        if task_type == task_comparative_analysis_standard and len(files) == 2 and len(parameters) == 3:
            reerr = self.start_comparative_analysis()
            if not reerr:
                for err in reerr:
                    if err not in self.error:
                        self.error.append(err)
                        
        elif task_type == task_permsearch and len(files) == 2 and len(parameters) == 0:
            reerr = self.start_permsearch()
            if not reerr:
                for err in reerr:
                    if err not in self.error:
                        self.error.append(err)
        else:
            self.error.append(1)
            

    def start_comparative_analysis(self) -> list:
        reerr = comparative_analysis.make_comparative_analysis(self.files, self.parameters[0], self.parameters[1], self.parameters[2])
        return reerr
    
    def start_permsearch(self) -> list:
        reerr = []
        thread_permsearch = threading.Thread(target=Permsearch.start_permsearch, args=(self.files, self.progress, self.progress_text, self.parameters))
        thread_permsearch.start()
        #print(thread_permsearch.is_alive())
        return reerr
    
    def get_task_status(self):
        self.progress = self.data_queue.get()
        return self.progress

    def get_error_code(self) -> list:
        return self.error