import tkinter as tk


class B3MApp:
    def __init__(self, master):
        self.master = master
        self.master.title("B3-M 距离监视器")

        # 直接设定为固定显示的数值
        self.distance_var = tk.StringVar(value="29.97 m")
        self.strength_var = tk.StringVar(value="90")
        self.status_var = tk.StringVar(value="串口已连接")  # 这里改成串口已连接

        # ======= 布局 =======
        tk.Label(master, text="当前距离：", font=("微软雅黑", 14)).grid(
            row=0, column=0, sticky="e", padx=10, pady=10
        )
        tk.Label(master, textvariable=self.distance_var, font=("微软雅黑", 18, "bold")).grid(
            row=0, column=1, sticky="w", padx=10, pady=10
        )

        tk.Label(master, text="信号强度：", font=("微软雅黑", 12)).grid(
            row=1, column=0, sticky="e", padx=10, pady=5
        )
        tk.Label(master, textvariable=self.strength_var, font=("微软雅黑", 12)).grid(
            row=1, column=1, sticky="w", padx=10, pady=5
        )

        tk.Label(master, text="状态：", font=("微软雅黑", 10)).grid(
            row=2, column=0, sticky="e", padx=10, pady=5
        )
        tk.Label(master, textvariable=self.status_var, font=("微软雅黑", 10)).grid(
            row=2, column=1, sticky="w", padx=10, pady=5
        )

        btn_frame = tk.Frame(master)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)

        close_btn = tk.Button(btn_frame, text="关闭窗口", command=self.master.destroy)
        close_btn.pack(side="left", padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = B3MApp(root)
    root.mainloop()
