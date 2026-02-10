# 中文速读器 + MSFT 实时股票分析工具

本仓库现在包含两个独立工具：

1. **中文速读器（GUI）**：使用 Python + Tkinter 开发，帮助进行中文快速阅读训练。
2. **微软股票实时分析工具（CLI）**：实时获取微软（`MSFT`）行情并计算常用技术指标，便于后续量化分析。

---

## 1) 中文速读器

一个简单的中文速读工具，使用 Python 和 Tkinter 开发。帮助提高阅读速度和理解能力。

### 功能特点

- 支持中文文本分词和智能组词
- 可调节阅读速度（词/分钟）
- 支持字体、字号、颜色自定义
- 智能分词：自动合并数字、量词、短语等
- 键盘快捷键控制：
  - 空格键：开始/暂停
  - 左右方向键：快退/快进20词
  - 上下方向键：增减速度（每次±100词/分钟）
- 支持暂停、继续和停止功能
- 界面简洁，操作直观

### 系统要求

- 操作系统：Windows/MacOS/Linux
- Python 3.6+

### 依赖项

- jieba：中文分词库
- tkinter：GUI界面库（Python标准库）

### 使用方法

```bash
pip install jieba
python main.py
```

---

## 2) 微软（MSFT）实时股票分析工具

文件：`msft_realtime_analyzer.py`

### 功能

- 实时拉取微软 `MSFT` 行情（Yahoo Finance 公共接口）
- 输出实时价格、涨跌额、涨跌幅
- 同时计算并输出常用技术指标：
  - `SMA5`
  - `SMA20`
  - `EMA12`
  - `RSI14`
- 可选保存为 CSV，便于后续用 Pandas / Excel / BI 工具做深入分析

### 快速开始

```bash
python msft_realtime_analyzer.py --interval 5 --samples 60
```

参数说明：

- `--interval`：刷新间隔秒数，默认 `5`
- `--samples`：采样次数，默认 `120`
- `--csv`：输出 CSV 文件路径（可选）

示例：

```bash
python msft_realtime_analyzer.py --interval 3 --samples 100 --csv data/msft_live.csv
```

### 输出示例

```text
[2026-01-01 22:31:15] MSFT 价格: 430.25 USD | 涨跌: +1.52 (+0.35%)
  指标 -> SMA5: 429.81 SMA20: 427.90 EMA12: 429.44 RSI14: 62.03
```

### 适合的分析场景

- 盘中波动观察
- 技术指标实时信号监控
- 为后续策略回测积累近实时数据样本

---

## 测试

```bash
python -m unittest -v
```

---

## 许可证

MIT License
