import tkinter as tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import subprocess
import threading
import time
from queue import *
import keywords

class Application:

    # load main window of application
    def __init__(self, master):
        self.current_script_file_name = None
        self.q = Queue()
        self.return_code = None;
        self.swift_keywords = keywords.SwiftKeywords()

        self.window = master
        self.window.title("TK")
        self.window.geometry("740x670")
        self.window.resizable(True, True)
        self.window.minsize(740, 670)
        self.window.maxsize(740,670)



        # create frame for buttons and create buttons
        self.frame_buttons = tk.Frame(master = self.window, relief = tk.RAISED, bd = 1)
        self.button_save = tk.Button(master = self.frame_buttons, text = "Save", command = self.save_script_to_file)
        self.button_run = tk.Button(master = self.frame_buttons, text = "Run", command = self.run_script_from_file)

        self.label_returncode_update = tk.StringVar()
        self.label_returncode = tk.Label(master = self.frame_buttons, textvariable = self.label_returncode_update, relief = tk.RAISED)
        self.label_returncode_update.set("Return Code\n")
        self.label_returncode.grid(row = 2, column = 0, sticky = "ew", padx = 5, pady = 5)

        self.label_is_script_executing = tk.StringVar()
        self.label_returncode = tk.Label(master = self.frame_buttons, textvariable = self.label_is_script_executing, relief = tk.RAISED)
        self.label_is_script_executing.set("Script Exec\nNo")
        self.label_returncode.grid(row = 3, column = 0, sticky = "ew", padx = 5, pady = 5)

        # create frame for tk.Text editor and output
        self.frame_text = tk.Frame(master = self.window, relief = tk.RAISED, bd = 1)
        self.text_editor = tk.Text(self.frame_text, height = 30, width = 80)
        self.text_output = tk.Text(self.frame_text, background = "Black", foreground = "White", height = 7, width = 80)

        #adjust buttons
        self.button_save.grid(row = 0, column = 0, sticky = "ew", padx = 5, pady = 5)
        self.button_run.grid(row = 1, column = 0, sticky = "ew", padx = 5, pady = 5)
        self.frame_buttons.grid(row = 0, column = 0, sticky = "ns")

        #adjust text editor and text output
        self.text_editor.grid(row = 0, column = 1, sticky = "ew", padx = 10, pady = 10)
        self.text_output.grid(row = 1, column = 1, sticky = "ew", padx = 5, pady = 5)
        self.frame_text.grid(row = 0, column = 1, sticky = "ns")

        self.text_output.insert(tk.END, 'Script Result:\n')
        self.text_output.config(state = 'disabled')
        self.update()

    def save_script_to_file(self):
        file_path = asksaveasfilename(
            filetypes=[("Python Scripts", "*.py"), ("Kotlin Scripts", "*.kts*")]
        )
        if not file_path:
            return
        with open(file_path, "w") as output_file:
            text = self.text_editor.get(1.0, tk.END)
            output_file.write("#!/usr/bin/env python3\n")
            output_file.write(text)

        self.window.title(f"Text Editor Application - {file_path}")

    def run_script_from_file(self):
        # start thread so main window not going to freeze
        threading.Thread(target=self.run_script).start()
        self.label_is_script_executing.set("Script Exec\nYes")

    def run_script(self):
        sub_proc = subprocess.Popen(['python3', '-u','script.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        thr1 = threading.Thread(target=self.pipe_reader, args=[sub_proc.stdout]).start()
        thr2 = threading.Thread(target=self.pipe_reader, args=[sub_proc.stderr]).start()

        poll = sub_proc.poll()
        while poll == None:
            time.sleep(1.)
            poll = sub_proc.poll()
        self.return_code = poll
        self.label_returncode_update.set("Return Code\n" + str(self.return_code))
        self.label_is_script_executing.set("Script Exec\nNo")


    def update(self):
        while not self.q.empty():
            source, line = self.q.get()
            if line is None:
                line = "\n"
            self.text_output.config(state = 'normal')
            self.text_output.insert(tk.END,line)
            self.text_output.see("insert")
            self.text_output.config(state = 'disabled')
        self.window.after(100, self.update)

    def pipe_reader(self, pipe):
        for line in iter(pipe.readline, b''):
            self.q.put((pipe, line))
        self.q.put((pipe, None))



if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    root.mainloop()