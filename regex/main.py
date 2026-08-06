import tkinter as tk
from tkinter import ttk, scrolledtext
import ctypes
import engine  # 导入我们写好的引擎模块


class RegexToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("正则工具箱")
        self.root.geometry("1024x1024")

        # 接入规则引擎
        self.engine = engine.global_engine

        # --- 核心状态变量 ---
        self.current_rule_name = tk.StringVar()
        self.auto_mode = tk.BooleanVar(value=True)  # 默认自动模式
        self.replace_job_id = None  # 用于存储 after() 返回的ID，以便取消计划任务

        # 初始化所有UI组件
        self.setup_ui()
        # 加载规则到下拉框，并初始更新一次
        self.load_rules()

        # 初始状态设置
        self.on_mode_toggled()  # 应用初始模式设置

    def setup_ui(self):
        """构建整个用户界面"""
        # 主框架
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(2, weight=1)  # 输入框行
        mainframe.rowconfigure(4, weight=1)  # 输出框行

        # ----- 第1行：规则选择与模式切换 -----
        ttk.Label(mainframe, text="选择规则:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.rule_combo = ttk.Combobox(mainframe, textvariable=self.current_rule_name,
                                       state="readonly", width=30)
        self.rule_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 20), pady=(0, 5))
        self.rule_combo.bind('<<ComboboxSelected>>', self.on_rule_selected)

        # 模式切换开关
        self.mode_switch = ttk.Checkbutton(mainframe, text="自动替换",
                                           variable=self.auto_mode,
                                           command=self.on_mode_toggled)
        self.mode_switch.grid(row=0, column=2, sticky=tk.W, pady=(0, 5))

        # ----- 第2行：规则描述 -----
        self.desc_label = ttk.Label(mainframe, text="", foreground="gray", wraplength=600)
        self.desc_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))

        # ----- 第3行：输入框 -----
        input_frame = ttk.LabelFrame(mainframe, text="输入文本", padding="5")
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)

        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, font=('Consolas', 10))
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 绑定内容修改事件
        self.input_text.bind('<<Modified>>', self.on_content_changed)

        # 输入框的复制按钮
        ttk.Button(input_frame, text="复制", command=self.copy_input,
                   width=8).grid(row=0, column=1, sticky=tk.NE, padx=(5, 0), pady=5)

        # ----- 第4行：替换按钮 -----
        btn_frame = ttk.Frame(mainframe)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.replace_btn = ttk.Button(btn_frame, text="替换",
                                      command=self.manual_replace, width=15)
        self.replace_btn.pack()

        # ----- 第5行：输出框 -----
        output_frame = ttk.LabelFrame(mainframe, text="输出文本", padding="5")
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD,
                                                     font=('Consolas', 10))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 输出框的复制按钮
        ttk.Button(output_frame, text="复制", command=self.copy_output,
                   width=8).grid(row=0, column=1, sticky=tk.NE, padx=(5, 0), pady=5)

    def load_rules(self):
        """加载规则到下拉框"""
        rule_names = self.engine.get_rule_names()
        if rule_names:
            self.rule_combo['values'] = rule_names
            self.current_rule_name.set(rule_names[0])
            self.update_rule_description()
        else:
            self.current_rule_name.set("无可用规则")
            self.desc_label.config(text="请在 rules/ 目录中添加规则文件")

    def update_rule_description(self):
        """更新规则描述"""
        rule_name = self.current_rule_name.get()
        rule = rule_name if rule_name == "无可用规则" else self.engine.get_rule_description(rule_name)
        self.desc_label.config(text=f"描述: {rule}")

    def on_rule_selected(self, event=None):
        """当选择规则时触发"""
        self.update_rule_description()
        # 自动模式下立即更新输出
        if self.auto_mode.get():
            self.schedule_update()

    def on_content_changed(self, event=None):
        """当输入框内容被修改时触发（包括粘贴）"""
        # 检查是否是用户修改（而不是程序设置）
        if self.input_text.edit_modified():
            if self.auto_mode.get():
                self.schedule_update()
            # 重置修改标志
            self.input_text.edit_modified(False)

    def schedule_update(self):
        """防抖调度：取消旧任务，计划新任务（50ms延迟）"""
        if self.replace_job_id:
            self.root.after_cancel(self.replace_job_id)
        self.replace_job_id = self.root.after(50, self.update_output)

    def update_output(self):
        """执行替换并更新输出框"""
        rule_name = self.current_rule_name.get()
        input_content = self.input_text.get("1.0", tk.END).strip()

        if not rule_name or rule_name == "无可用规则" or not input_content:
            self.set_output_text("")
            return

        # 执行替换
        result = self.engine.apply_rule(rule_name, input_content)
        self.set_output_text(result)

    def set_output_text(self, text):
        """安全地设置输出框内容"""
        self.output_text.config(state='normal')
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        # 根据模式设置输出框状态
        if self.auto_mode.get():
            self.output_text.config(state='disabled')

    def manual_replace(self):
        """手动替换按钮的回调函数"""
        if not self.auto_mode.get():  # 仅在手动模式下有效
            self.update_output()

    def on_mode_toggled(self):
        """当模式切换时调用"""
        is_auto = self.auto_mode.get()

        # 更新替换按钮状态
        if is_auto:
            self.replace_btn.config(state='disabled')
            self.output_text.config(state='disabled')
            # 切换到自动模式时：清空输出框，并根据当前输入更新
            self.output_text.delete("1.0", tk.END)
            if self.input_text.get("1.0", "end-1c"):  # 如果有输入内容
                self.schedule_update()
        else:
            self.replace_btn.config(state='normal')
            self.output_text.config(state='normal')
            # 切换到手动模式时：清空输出框
            self.output_text.delete("1.0", tk.END)
            # 取消任何待定的自动更新
            if self.replace_job_id:
                self.root.after_cancel(self.replace_job_id)
                self.replace_job_id = None

    def copy_input(self):
        """复制输入框内容到剪贴板"""
        text = self.input_text.get("1.0", tk.END).rstrip('\n')
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def copy_output(self):
        """复制输出框内容到剪贴板"""
        text = self.output_text.get("1.0", tk.END).rstrip('\n')
        self.root.clipboard_clear()
        self.root.clipboard_append(text)


def main():
    # ==========修复Windows高DPI模糊 重点==========
    import os
    if os.name == 'nt':
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    # ============================================
    root = tk.Tk()
    app = RegexToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
