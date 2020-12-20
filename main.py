import tkinter as tk
import subprocess
import threading
import time
from queue import *
import keywords
import os

class Application:

    # load main window of application
    def __init__(self, master):
        
        self.current_script_file_name = "scr.swift"
        self.subprocess_pipe_q = Queue()
        self.script_return_code = None;
        self.swift_keywords = keywords.SwiftKeywords()

        # configure main window
        self.window = master
        self.window.title("JetBrains Swift Script Executing Tool")
        self.window.minsize(680,680)
        self.window.configure(bg = "#1c3e7b")

        # load icons for buttons
        self.run_icon = tk.PhotoImage(file = "resources/rsz_run.png")
        self.save_icon = tk.PhotoImage(file = "resources/rsz_save.png")

        # top bar buttons
        self.frame_buttons = tk.Frame(master= self.window, height = 200, width = 200, bg = "#1c3e7b")
        self.button_save = tk.Button(master = self.frame_buttons,
                                    image = self.save_icon, 
                                    bg = "#1c3e7b",
                                    activebackground = "#1c3e60",
                                    relief = "flat",
                                    highlightthickness = 0,
                                    bd = 0,
                                    command = self.button_save_script_on_clicked
                                    )

        self.button_run = tk.Button(master = self.frame_buttons,
                                    image = self.run_icon, 
                                    bg = "#1c3e7b",
                                    activebackground = "#1c3e60", 
                                    relief = "flat",
                                    highlightthickness = 0, 
                                    bd = 0,
                                    command = self.button_run_script_on_clicked
                                    )

        self.frame_buttons.pack(side = "top", fill = "both", expand = False)
        self.button_run.pack(side = "left")
        self.button_save.pack(side = "left")

        # editor pane and output pane
        self.text_editor = tk.Text(self.window, bg = "#232614", foreground = "White", insertbackground='white')
        self.text_editor.pack(side = "top", expand = True, fill = "both", padx = 5, pady = 5)
        self.text_editor.tag_configure("keyword", foreground = "red")
        self.text_output = tk.Text(self.window, background = "Black", foreground = "White", height = 8)
        self.text_output.pack(side = "top", expand = True, fill = "both", padx = 5, pady = 5)

        # indicators (return code and is script executing)
        self.frame_label = tk.Frame(master = self.window, bg = "#1c3e7b")
        self.frame_label.pack(side = "top", expand = False, fill = "both")

        # label for script return code
        self.label_returncode_update = tk.StringVar()
        self.label_returncode = tk.Label(master = self.frame_label, 
                                            textvariable = self.label_returncode_update, 
                                            bg = "#1c3e7b", foreground = "#ffffff")

        self.label_returncode_update.set("Return Code\n")
        self.label_returncode.pack(side = "left", padx = 3, pady = 3)

        # label for is script executing
        self.label_is_script_executing = tk.StringVar()
        self.label_script_executing = tk.Label(master = self.frame_label,
                                                textvariable = self.label_is_script_executing, 
                                                bg = "#1c3e7b", foreground = "#ffffff")

        self.label_is_script_executing.set("Script Exec\nNo")
        self.label_script_executing.pack(side = "left", padx = 3, pady = 3)


        # pane config
        self.text_output.insert(tk.END, 'Script Result:\n')
        self.text_output.config(state = 'disabled')        

        # check after every space if previous word is keyword of language
        self.text_editor.bind("<space>", self.swift_keywords_highlight)

        # refresh output pane every 0.1
        self.update_output_pane()



    def button_save_script_on_clicked(self):
        cwd = os.getcwd()
        file_name = cwd + "/" + self.current_script_file_name
        with open(file_name, "w") as output_file:
            text = self.text_editor.get(1.0, tk.END)
            output_file.write(text)



    def button_run_script_on_clicked(self):
        #self.button_save_script_on_clicked()
        # start thread so main window not going to freeze
        threading.Thread(target=self.button_run_script_thread).start()
        self.label_is_script_executing.set("Script Exec\nYes")
        self.button_run.config(state = 'disabled')



    def button_run_script_thread(self):
        sub_proc = subprocess.Popen(['stdbuf', '-o0','swift', 'script2.swift'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        threading.Thread(target=self.button_run_pipe_reader, args=[sub_proc]).start()

        poll = sub_proc.poll()
        while poll == None:
            time.sleep(.2)
            poll = sub_proc.poll()
        self.script_return_code = poll
        self.label_returncode_update.set("Return Code\n" + str(self.script_return_code))
        self.button_run.config(state = 'normal')
        self.label_is_script_executing.set("Script Exec\nNo")
        sub_proc.kill()



    def button_run_pipe_reader(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.subprocess_pipe_q.put(output)



    def swift_keywords_highlight(self, event):
        index = self.text_editor.search(r'\s', "insert", backwards=True, regexp=True)
        if index == "":
            index = "1.0"
        else:
            index = self.text_editor.index("%s+1c" % index)
        word = self.text_editor.get(index, "insert")
        if self.swift_keywords.is_keyword(word):
            self.text_editor.tag_add("keyword", index, "%s+%dc" % (index,len(word)))
        else:
            self.text_editor.tag_remove("keyword", index, "%s+%dc" % (index,len(word)))



    def update_output_pane(self):
        while not self.subprocess_pipe_q.empty():
            line = self.subprocess_pipe_q.get()
            if line is None:
                line = ""
            self.text_output.config(state = 'normal')
            self.text_output.insert(tk.END,line)
            self.text_output.see("insert")
            self.text_output.config(state = 'disabled')
        self.window.after(100, self.update_output_pane)



if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
    root.quit()