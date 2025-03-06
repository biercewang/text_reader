import tkinter as tk
from tkinter import ttk, scrolledtext
import re
import time
import threading
import jieba
import logging

# 设置结巴分词的日志级别为 WARNING，隐藏初始化信息
jieba.setLogLevel(logging.WARNING)

class SpeedReader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("速读器")
        self.root.geometry("800x600")
        
        # 设置窗口居中显示
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口位置
        window_width = 800
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 初始化状态变量
        self.is_reading = False
        self.is_paused = False  # 添加暂停状态标志
        self.reading_thread = None
        self.current_word_index = 0  # 添加当前词索引
        self.words = []  # 添加词列表存储
        
        # 绑定键盘事件
        self.root.bind('<space>', self.toggle_reading)
        self.root.bind('<Left>', self.rewind)
        self.root.bind('<Right>', self.forward)
        self.root.bind('<Up>', self.increase_speed)
        self.root.bind('<Down>', self.decrease_speed)
        
        # 添加需要合并的词类
        self.auxiliary_words = {
            '的', '地', '得', '了', '着', '过', '吗', '呢', '啊', '吧', '么',  # 助词
            '个', '只', '条', '张', '位', '块', '支', '本', '件', '双', '群', '对', '番',  # 常用量词
            '和', '与', '及', '跟', '把', '被', '让', '给', '对', '向', '从', '由',  # 介词连词
            '也', '都', '就', '才', '会', '要', '可', '能', '将', '在', '很', '更', '最',  # 副词、情态词
            '这', '那', '些', '此', '该', '每', '某', '任',  # 指示词
            '之', '所', '以', '为', '而', '却', '且', '并', '或', '但',  # 其他虚词
            '一', '两', '几', '多', '些',  # 数词
            '里', '上', '下', '中', '内', '外', '前', '后', '左', '右',  # 方位词
            '年', '月', '日', '时', '分', '秒',  # 时间单位
        }
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # 输入区域
        self.input_label = ttk.Label(self.main_frame, text="请输入或粘贴文本：")
        self.input_label.pack()
        
        self.text_input = scrolledtext.ScrolledText(self.main_frame, height=10)
        self.text_input.pack(fill='x', pady=5)
        
        # 控制区域
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill='x', pady=5)
        
        # 速度设置
        self.speed_label = ttk.Label(self.control_frame, text="速度(词/分钟)：")
        self.speed_label.pack(side='left')
        
        self.speed_var = tk.StringVar(value="300")  # 修改默认速度为600
        self.speed_entry = ttk.Entry(self.control_frame, textvariable=self.speed_var, width=10)
        self.speed_entry.pack(side='left', padx=5)
        
        # 字体设置区域
        self.font_frame = ttk.LabelFrame(self.control_frame, text="字体设置")
        self.font_frame.pack(side='left', padx=10)
        
        # 字体选择
        self.font_family_var = tk.StringVar(value="Arial")
        self.font_families = ["Arial", "微软雅黑", "宋体", "黑体", "楷体"]
        self.font_combo = ttk.Combobox(self.font_frame, textvariable=self.font_family_var, 
                                     values=self.font_families, width=10)
        self.font_combo.pack(side='left', padx=5)
        
        # 字号选择
        self.font_size_var = tk.StringVar(value="24")
        self.font_sizes = ["16", "20", "24", "28", "32", "36", "40"]
        self.size_combo = ttk.Combobox(self.font_frame, textvariable=self.font_size_var, 
                                     values=self.font_sizes, width=5)
        self.size_combo.pack(side='left', padx=5)
        
        # 颜色选择
        self.color_var = tk.StringVar(value="black")
        self.colors = ["black", "red", "blue", "green", "purple"]
        self.color_combo = ttk.Combobox(self.font_frame, textvariable=self.color_var, 
                                      values=self.colors, width=8)
        self.color_combo.pack(side='left', padx=5)
        
        # 绑定字体更新事件
        self.font_combo.bind('<<ComboboxSelected>>', self.update_font)
        self.size_combo.bind('<<ComboboxSelected>>', self.update_font)
        self.color_combo.bind('<<ComboboxSelected>>', self.update_font)
        
        self.start_button = ttk.Button(self.control_frame, text="▶", command=self.start_reading)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(self.control_frame, text="⏹", command=self.stop_reading)
        self.stop_button.pack(side='left', padx=5)
        
        # 显示区域
        self.display_frame = ttk.Frame(self.main_frame, height=200)
        self.display_frame.pack(expand=True, fill='both')
        
        # 创建固定宽度的显示容器，使用 Label 而不是 Frame
        self.word_label = ttk.Label(self.display_frame, 
                                  text="", 
                                  font=(self.font_family_var.get(), int(self.font_size_var.get())),
                                  width=20,  # 设置固定宽度
                                  anchor='w')  # 文本左对齐
        self.word_label.place(relx=0.5, rely=0.5, anchor='w')  # 使用 place 布局，左对齐
        self.word_label.pack(side='left')
        self.word_label.place(relx=0.5, rely=0.5, anchor='center')

    def update_font(self, event=None):
        """更新显示文本的字体设置"""
        self.word_label.configure(
            font=(self.font_family_var.get(), int(self.font_size_var.get())),
            foreground=self.color_var.get()
        )

    def split_text(self, text):
        # 移除 Markdown 标记
        text = re.sub(r'#.*?\n', '', text)
        text = re.sub(r'\[.*?\]|\(.*?\)', '', text)
        text = re.sub(r'[*_~`]', '', text)
        
        words = []
        current_word = ""
        last_word_type = None
        
        # 使用结巴分词处理中文（移除 paddle 模式）
        segments = list(jieba.cut(text))
        
        for i, seg in enumerate(segments):
            if not seg.strip():
                continue
            
            # 如果是括号，附加到当前词组或与下一个词组合并
            if re.match(r'^[（）()\[\]{}【】「」『』]$', seg):
                if current_word:
                    current_word += seg
                elif i + 1 < len(segments):
                    current_word = seg
                else:
                    words.append(seg)
                continue
            
            # 如果是标点符号，附加到当前词组
            if re.match(r'^[，。！？,.!?、：:；;]$', seg):
                if current_word:
                    current_word += seg
                else:
                    words.append(seg)
                continue
            
            # 如果是虚词，附加到当前词组
            if seg in self.auxiliary_words:
                if current_word:
                    current_word += seg
                    continue
            
            # 检查下一个词，判断是否需要合并
            next_seg = segments[i + 1] if i + 1 < len(segments) else None
            
            # 合并规则
            should_merge = False
            if next_seg:
                # 数字和量词组合（如：51个、3只）
                if re.match(r'^[一二三四五六七八九十百千万亿\d]+$', seg):
                    if next_seg in self.auxiliary_words or re.match(r'^[一二三四五六七八九十百千万亿\d]+$', next_seg):
                        should_merge = True
                # 形容词和名词组合（如：美丽的花）
                elif len(seg) == 1 and next_seg in self.auxiliary_words:
                    should_merge = True
                # 动词和补语组合（如：看见、走到）
                elif len(seg) == 1 and len(next_seg) == 1:
                    should_merge = True
                # 括号和其他字符的组合
                elif re.match(r'^[（）()\[\]{}【】「」『』]$', next_seg):
                    should_merge = True
            
            if should_merge:
                if current_word:
                    current_word += seg
                else:
                    current_word = seg
            else:
                if current_word:
                    words.append(current_word)
                current_word = seg
        
        # 处理最后一个词组
        if current_word:
            words.append(current_word)
        
        return words

    def toggle_reading(self, event=None):
        """空格键控制暂停/继续"""
        if not self.words:
            text = self.text_input.get("1.0", tk.END)
            self.words = self.split_text(text)
            
        if self.is_reading:
            # 暂停
            self.is_reading = False
            self.is_paused = True
            self.word_label.config(text=self.words[self.current_word_index])
            self.start_button.config(text="▶")  # 更新按钮图标为播放
        elif self.is_paused:
            # 继续
            self.is_paused = False
            self.is_reading = True
            self.start_button.config(text="⏸")  # 更新按钮图标为暂停
            self.display_words(self.words, 60.0 / int(self.speed_var.get()), self.current_word_index)
        else:
            # 开始
            self.is_paused = False
            self.is_reading = True
            self.start_button.config(text="⏸")  # 更新按钮图标为暂停
            self.start_reading(start_index=0)

    def stop_reading(self):
        """停止阅读"""
        self.is_reading = False
        self.is_paused = False  # 重置暂停状态
        self.current_word_index = 0  # 重置位置
        self.start_button.config(text="▶")  # 更新按钮图标为播放
        # 只有在非暂停状态下才清空显示
        if not self.is_paused:
            self.word_label.config(text="")

    def display_words(self, words, delay, start_index=0):
        delay_ms = int(delay * 1000)
        word_index = start_index
        
        def show_next_word():
            nonlocal word_index
            if not self.is_reading:
                if not self.is_paused:  # 只有在非暂停状态下才清空显示
                    self.word_label.config(text="")
                return
            
            if word_index >= len(words):
                self.is_reading = False
                if not self.is_paused:  # 只有在非暂停状态下才清空显示
                    self.word_label.config(text="")
                return
                
            self.word_label.config(text=words[word_index])
            self.current_word_index = word_index
            word_index += 1
            self.root.after(delay_ms, show_next_word)
        
        show_next_word()

    def rewind(self, event=None):
        """后退20个词"""
        if not self.words:
            return
        self.current_word_index = max(0, self.current_word_index - 20)
        self.word_label.config(text=self.words[self.current_word_index])  # 更新显示的文字
        if self.is_reading:
            self.stop_reading()
            self.start_reading(start_index=self.current_word_index)

    def forward(self, event=None):
        """前进20个词"""
        if not self.words:
            return
        self.current_word_index = min(len(self.words) - 1, self.current_word_index + 20)
        self.word_label.config(text=self.words[self.current_word_index])  # 更新显示的文字
        if self.is_reading:
            self.stop_reading()
            self.start_reading(start_index=self.current_word_index)

    def decrease_speed(self, event=None):
        """减少速度100词/分钟"""
        try:
            current_speed = int(self.speed_var.get())
            new_speed = max(100, current_speed - 100)  # 最小速度为100
            self.speed_var.set(str(new_speed))
            # 立即重新计算延迟时间并重启阅读
            if self.is_reading:
                self.restart_reading()
        except ValueError:
            pass

    def increase_speed(self, event=None):
        """增加速度100词/分钟"""
        try:
            current_speed = int(self.speed_var.get())
            self.speed_var.set(str(current_speed + 100))
            # 立即重新计算延迟时间并重启阅读
            if self.is_reading:
                self.restart_reading()
        except ValueError:
            pass

    def restart_reading(self):
        """重新开始阅读（保持当前位置和文本）"""
        self.stop_reading()
        # 确保在重新开始前等待一小段时间
        self.root.after(100, lambda: self.start_reading(start_index=self.current_word_index))

    def start_reading(self, start_index=None):
        if self.is_reading or self.is_paused:
            return
            
        # 如果是首次开始阅读，需要获取并处理文本
        if not self.words:
            text = self.text_input.get("1.0", tk.END)
            self.words = self.split_text(text)
        
        # 设置起始位置
        if start_index is not None:
            self.current_word_index = start_index
        else:
            self.current_word_index = 0
        
        try:
            wpm = int(self.speed_var.get())
            delay = 60.0 / wpm
        except ValueError:
            delay = 0.2
            
        self.is_reading = True
        self.is_paused = False
        self.display_words(self.words, delay, self.current_word_index)

    def display_words(self, words, delay, start_index=0):
        delay_ms = int(delay * 1000)
        word_index = start_index
        
        def show_next_word():
            nonlocal word_index
            if not self.is_reading or word_index >= len(words):
                if not self.is_paused:  # 只有在非暂停状态下才清空显示
                    self.word_label.config(text="")
                self.is_reading = False
                return
                
            self.word_label.config(text=words[word_index])
            self.current_word_index = word_index
            word_index += 1
            self.root.after(delay_ms, show_next_word)
        
        show_next_word()

    def run(self):
        self.root.mainloop()

    def stop_reading(self):
        """停止阅读"""
        self.is_reading = False
        self.word_label.config(text="")

if __name__ == "__main__":
    try:
        app = SpeedReader()
        app.run()
    except Exception as e:
        print(f"程序运行出错: {str(e)}")