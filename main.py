import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import jieba
import re

class SpeedReaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("速读器")
        self.is_reading = False
        self.words = []  # 确保在setup_ui之前初始化words
        self.index = 0
        self.after_id = None  # 新增：用于保存after事件ID
        jieba.setLogLevel(20)
        self.setup_ui()  # 移到初始化变量之后

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
        
        # 添加显示行数选择
        ttk.Label(control_frame, text="显示行数：").pack(side='left', padx=5)
        self.lines_var = tk.IntVar(value=1)
        lines_combo = ttk.Combobox(control_frame, textvariable=self.lines_var, values=[1, 3, 5, 7, 9, 11, 13, 15], width=3, state="readonly")
        lines_combo.pack(side='left')
        lines_combo.bind("<<ComboboxSelected>>", lambda e: self.update_display_lines())

        ttk.Button(control_frame, text="开始/暂停", command=self.toggle_reading).pack(side='left', padx=5)
        ttk.Button(control_frame, text="导入文本", command=self.load_file).pack(side='left', padx=5)

        # 修改标签显示区域
        self.display_frame = ttk.Frame(self.root)
        self.display_frame.pack(expand=True, fill='both')
        
        # 初始化显示（默认1行）
        self.update_display_lines()
        
        self.progress = ttk.Progressbar(self.root)
        self.progress.pack(fill='x', padx=10, pady=5)

        # 键盘快捷键绑定
        self.root.bind("<space>", lambda e: self.toggle_reading())
        self.root.bind("<Left>", lambda e: self.change_index(-20))
        self.root.bind("<Right>", lambda e: self.change_index(20))
        self.root.bind("<Up>", lambda e: self.change_speed(100))
        self.root.bind("<Down>", lambda e: self.change_speed(-100))

    def update_font(self):
        # 更新所有标签的字体大小，保持中间标签字体更大
        base_size = self.font_size_var.get()
        self.prev_word_label.config(font=("微软雅黑", int(base_size * 0.75)))
        self.word_label.config(font=("微软雅黑", base_size))
        self.next_word_label.config(font=("微软雅黑", int(base_size * 0.75)))

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt;*.md")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert(tk.END, file.read())
    
    # 添加更新显示行数的方法
    def update_display_lines(self):
        # 清除现有的标签
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # 根据选择的行数创建标签
        lines = self.lines_var.get()
        self.word_labels = []
        
        base_size = self.font_size_var.get()
        middle_index = lines // 2
        
        # 创建一个Frame来容纳所有标签，并使其在display_frame中居中
        labels_container = ttk.Frame(self.display_frame)
        labels_container.pack(expand=True, fill='both')
        
        # 添加一个弹性空间在顶部，使标签组在垂直方向居中
        ttk.Frame(labels_container).pack(expand=True)
        
        # 创建标签，设置渐变的字体大小和颜色
        for i in range(lines):
            # 计算与中间行的距离
            distance = abs(i - middle_index)
            
            # 根据距离计算字体大小，距离越远字体越小
            size_factor = max(0.5, 1 - distance * 0.1)  # 最小为原始大小的50%
            font_size = int(base_size * size_factor)
            
            # 根据距离计算颜色深浅，距离越远颜色越浅
            # 中间行为黑色(#000000)，向两边逐渐变淡
            # 计算灰度值：0为黑色，255为白色，距离越远灰度值越大（越浅）
            gray_value = min(230, distance * 50)  # 最浅为#E6E6E6，避免完全变白
            color_hex = f'#{gray_value:02x}{gray_value:02x}{gray_value:02x}'
            
            label = ttk.Label(labels_container, text="", font=("微软雅黑", font_size), anchor='center', foreground=color_hex)
            label.pack(fill='x', pady=2)
            self.word_labels.append(label)
        
        # 添加一个弹性空间在底部，使标签组在垂直方向居中
        ttk.Frame(labels_container).pack(expand=True)
        
        # 如果有单词，更新显示
        if self.words and len(self.words) > 0:
            self.update_word_display()

    def split_text(self, text):
        text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
        words = list(jieba.cut(text))
        
        # 处理"的"等助词，将其与前面的词合并
        result = []
        i = 0
        while i < len(words):
            if i < len(words) - 1 and words[i+1] in ['的', '地', '得', '了', '着', '过']:
                result.append(words[i] + words[i+1])
                i += 2
            else:
                result.append(words[i])
                i += 1
        
        return result

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

        self.update_word_display()
        
        self.progress['value'] = self.index
        delay = int(60000 / self.speed_var.get())
        self.index += 1
        self.after_id = self.root.after(delay, self.display_word)
    
    # 添加更新单词显示的方法
    def update_word_display(self):
        lines = self.lines_var.get()
        middle_index = lines // 2
        
        for i in range(lines):
            word_index = self.index - middle_index + i
            if 0 <= word_index < len(self.words):
                word = self.words[word_index]
                # 中间行使用 >词< 格式，其他行直接显示词语
                if i == middle_index:
                    self.word_labels[i].config(text=f">{word}<" if word else "")
                else:
                    self.word_labels[i].config(text=word if word else "")
            else:
                self.word_labels[i].config(text="")
    
    def change_index(self, delta):
        self.index = max(0, min(len(self.words)-1, self.index + delta))
        self.progress['value'] = self.index
        
        # 更新单词显示
        self.update_word_display()

    def change_speed(self, delta):
        new_speed = max(100, self.speed_var.get() + delta)
        self.speed_var.set(new_speed)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SpeedReaderApp()
    app.run()