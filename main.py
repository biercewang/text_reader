import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import jieba
import re

class SpeedReaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("速读器")
        self.setup_ui()
        self.is_reading = False
        self.words = []
        self.index = 0
        self.after_id = None  # 新增：用于保存after事件ID
        jieba.setLogLevel(20)

    def setup_ui(self):
        self.root.geometry('800x600+{}+{}'.format(
            (self.root.winfo_screenwidth()-800)//2,
            (self.root.winfo_screenheight()-600)//2
        ))

        self.text_input = scrolledtext.ScrolledText(self.root, height=10)
        self.text_input.pack(fill='x', padx=10, pady=5)

        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=5)

        ttk.Label(control_frame, text="速度(词/分钟)：").pack(side='left')
        self.speed_var = tk.IntVar(value=300)
        ttk.Entry(control_frame, textvariable=self.speed_var, width=8).pack(side='left', padx=5)

        ttk.Label(control_frame, text="字体大小：").pack(side='left', padx=5)
        self.font_size_var = tk.IntVar(value=24)
        ttk.Spinbox(control_frame, from_=12, to=72, textvariable=self.font_size_var, width=5, command=self.update_font).pack(side='left')

        ttk.Button(control_frame, text="开始/暂停", command=self.toggle_reading).pack(side='left', padx=5)
        ttk.Button(control_frame, text="导入文本", command=self.load_file).pack(side='left', padx=5)

        self.word_label = ttk.Label(self.root, text="", font=("微软雅黑", 24))
        self.word_label.pack(expand=True)

        self.progress = ttk.Progressbar(self.root)
        self.progress.pack(fill='x', padx=10, pady=5)

        # 键盘快捷键绑定
        self.root.bind("<space>", lambda e: self.toggle_reading())
        self.root.bind("<Left>", lambda e: self.change_index(-20))
        self.root.bind("<Right>", lambda e: self.change_index(20))
        self.root.bind("<Up>", lambda e: self.change_speed(100))
        self.root.bind("<Down>", lambda e: self.change_speed(-100))

    def update_font(self):
        self.word_label.config(font=("微软雅黑", self.font_size_var.get()))

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt;*.md")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert(tk.END, file.read())

    def split_text(self, text):
        text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
        return list(jieba.cut(text))

    def toggle_reading(self):
        if not self.words:
            self.words = self.split_text(self.text_input.get("1.0", tk.END))
            self.progress.config(maximum=len(self.words))

        if self.is_reading:
            self.is_reading = False
            if self.after_id:
                self.root.after_cancel(self.after_id)  # 检查并取消定时器
                self.after_id = None
        else:
            self.is_reading = True
            # 将焦点设置到主窗口，避免空格键被其他控件捕获
            self.root.focus_set()
            self.display_word()

    def display_word(self):
        if not self.is_reading or self.index >= len(self.words):
            self.is_reading = False
            return

        word = self.words[self.index]
        highlighted_word = f"[{word}]" if word else ""
        self.word_label.config(text=highlighted_word)

        self.progress['value'] = self.index
        delay = int(60000 / self.speed_var.get())
        self.index += 1
        self.after_id = self.root.after(delay, self.display_word)  # 存储after_id

    def change_index(self, delta):
        self.index = max(0, min(len(self.words)-1, self.index + delta))
        self.progress['value'] = self.index
        self.word_label.config(text=self.words[self.index])

    def change_speed(self, delta):
        new_speed = max(100, self.speed_var.get() + delta)
        self.speed_var.set(new_speed)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SpeedReaderApp()
    app.run()