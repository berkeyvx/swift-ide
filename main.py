import tkinter as tk
import subprocess
import threading
import time
from queue import *
import keywords
import os
import re

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
        self.text_output.tag_configure("error", foreground = "red")
        self.text_output.tag_bind("error", "<Button-1>", self.error_move_cursor_text_editor)
        self.text_output.tag_bind("error", "<Enter>", self.show_hand_cursor)
        self.text_output.tag_bind("error", "<Leave>", self.hide_hand_cursor)

        # indicators (return code and is script executing)
        self.frame_label = tk.Frame(master = self.window, bg = "#1c3e7b")
        self.frame_label.pack(side = "top", expand = False, fill = "both")

        # label for script return code
        self.label_returncode_update = tk.StringVar()
        self.label_returncode = tk.Label(master = self.frame_label, 
                                            textvariable = self.label_returncode_update, 
                                            bg = "#1c3e7b", foreground = "#ffffff")

        self.label_returncode_update.set("Return Code: NULL")
        self.label_returncode.pack(side = "left", padx = 3, pady = 3)

        # label for is script executing
        self.label_is_script_executing = tk.StringVar()
        self.label_script_executing = tk.Label(master = self.frame_label,
                                                textvariable = self.label_is_script_executing, 
                                                bg = "#1c3e7b", foreground = "#ffffff")

        self.label_is_script_executing.set("Script Exec: No")
        self.label_script_executing.pack(side = "left", padx = 3, pady = 3)


        # pane config
        self.text_output.config(state = 'disabled')        

        # refresh output pane every 0.1, refresh editor pane every 0.3 sec
        self.update_output_pane()
        self.update_editor_pane()


    def button_save_script_on_clicked(self):
        cwd = os.getcwd()
        file_name = cwd + "/" + self.current_script_file_name
        with open(file_name, "w") as output_file:
            text = self.text_editor.get(1.0, tk.END)
            output_file.write(text)



    def button_run_script_on_clicked(self):
        self.button_save_script_on_clicked()
        self.text_output.config(state = 'normal')
        self.text_output.delete('1.0', tk.END)
        self.text_output.config(state = 'disabled')
        # start thread so main window not going to freeze
        threading.Thread(target=self.button_run_script_thread).start()
        self.label_is_script_executing.set("Script Exec: Yes")
        self.button_run.config(state = 'disabled')



    def button_run_script_thread(self):
        sub_proc = subprocess.Popen(['stdbuf', '-o0','swift', self.current_script_file_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        threading.Thread(target=self.button_run_pipe_reader, args=[sub_proc]).start()

        poll = sub_proc.poll()
        while poll == None:
            time.sleep(.2)
            poll = sub_proc.poll()
        self.script_return_code = poll
        self.output_pane_clickable_errors()
        self.label_returncode_update.set("Return Code: " + str(self.script_return_code))
        self.button_run.config(state = 'normal')
        self.label_is_script_executing.set("Script Exec: No")
        sub_proc.kill()



    def button_run_pipe_reader(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.subprocess_pipe_q.put(output)



    def update_editor_pane(self):
        self.text_editor.tag_remove("keyword","1.0",tk.END)
        itr = "1.0"
        last_space = "1.0"
        prev_itr = itr;
        while True:
            itr = self.text_editor.search(" ",itr, tk.END)
            if not itr:
                break
            if prev_itr.split(".")[0] != itr.split(".")[0]:
                itr = itr.split(".")[0] + ".0"
                itr = self.text_editor.search(" ",itr, tk.END)
                last_space = itr.split(".")[0] + ".0"
            last_itr = '%s+%dc' % (itr,len(" "))
            word = self.text_editor.get("%s" % last_space, itr)
            if self.swift_keywords.is_keyword(word):
                self.text_editor.tag_add("keyword",last_space, itr)
            itr = last_itr
            last_space = last_itr
            prev_itr = itr
        self.window.after(300, self.update_editor_pane)
        


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



    def output_pane_clickable_errors(self):
        pattern = "swift:[0-9]+:[0-9]+:"
        start = "1.0"
        end = self.text_output.index(tk.END)
        output = self.text_output.get(start, end)

        indices = []
        if output:
            matches = re.finditer(pattern, output)
            for match in matches:
                match_start = self.text_output.index("%s+%dc" % (start, match.start()))
                match_end = self.text_output.index("%s+%dc" % (start, match.end()))
                self.text_output.tag_add("error",match_start, match_end)

        

    def error_move_cursor_text_editor(self, event):
        x = event.widget.index("@%d,%d" % (event.x, event.y))
        data = event.widget.tag_ranges("error")
        z = zip(data[0::2], data[1::2])
        for i,k in z:
            # compare tag_randes with mouse event(x,y) and match with string
            bool_1 = self.text_output.compare(x, ">=", str(i))
            bool_2 = self.text_output.compare(x, "<=", str(k))
            if bool_1 and bool_2:
                error_code = self.text_output.get(i,k)
        line_char = re.findall(r'\b\d+\b', error_code)
        self.text_editor.mark_set("insert", "%d.%d" % (int(line_char[0]), int(line_char[1])))



    def show_hand_cursor(self, event):
        self.text_output.config(cursor="hand2")



    def hide_hand_cursor(self, event):
        self.text_output.config(cursor='')



    def quit(self):
        self.window.destroy()
                



if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    root.protocol("WM_DELETE_WINDOW", app.quit)
    root.mainloop()
    root.quit()