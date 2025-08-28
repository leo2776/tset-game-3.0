import tkinter as tk
from tkinter import messagebox
import random, time, os, sys, subprocess
import threading
import pygame

# ------------------- 模式設定 -------------------
DEVELOP_MODE = True  # True = 開發版，False = 玩家版

# ------------------- 遊戲主程式 -------------------
class TouchTestGame:
    def __init__(self, root):
        self.root = root
        self.root.title("觸控/滑鼠測試遊戲")
        self.root.geometry("900x700")
        
        # Canvas (白底)
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(pady=10)
        
        # 軌跡
        self.trail_max = 20
        self.trails = {}
        self.canvas.bind("<Motion>", self.mouse_move)
        self.canvas.bind("<B1-Motion>", self.touch_move)
        self.canvas.bind("<Button-1>", self.mouse_click)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_release)
        
        # 提示文字
        self.label = tk.Label(root, text="", font=("Arial", 16))
        self.label.pack()
        
        # 音樂
        pygame.mixer.init()
        threading.Thread(target=self.load_and_play_music, daemon=True).start()
        
        # 遊戲狀態
        self.current_circles = []
        self.current_level = 1
        self.min_longpress_time = 0.8  # 初始長按門檻
        
        # 開發版打包按鈕
        if DEVELOP_MODE:
            self.pack_button = tk.Button(root, text="打包遊戲為 EXE", font=("Arial",14), command=self.pack_game)
            self.pack_button.pack(pady=5)
        
        self.start_level()
    
    # ------------------- 音樂 -------------------
    def load_and_play_music(self):
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        music_file = os.path.join(exe_dir, "bgm.mp3")
        if os.path.isfile(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        else:
            print("bgm.mp3 不存在，請放在同目錄下")
    
    # ------------------- 軌跡 -------------------
    def mouse_move(self, event):
        self.draw_trail(event.x, event.y, "blue", "mouse")
    def touch_move(self, event):
        self.draw_trail(event.x, event.y, "green", f"touch{event.num}")
    def draw_trail(self, x, y, color, id):
        if id not in self.trails:
            self.trails[id] = []
        dot = self.canvas.create_oval(x-5,y-5,x+5,y+5,fill=color,outline="")
        self.trails[id].append(dot)
        if len(self.trails[id]) > self.trail_max:
            old_dot = self.trails[id].pop(0)
            self.canvas.delete(old_dot)
    
    # ------------------- 遊戲圓圈 -------------------
    def start_level(self):
        self.canvas.delete("all")
        self.current_circles.clear()
        num_circles = min(4 + self.current_level, 10)  # 每關增加圓圈數量
        self.label.config(text=f"關卡 {self.current_level}：按提示操作圓圈")
        
        generated = 0
        attempts = 0
        positions = []
        while generated < num_circles and attempts < 200:
            x = random.randint(100,700)
            y = random.randint(100,500)
            # 圓圈間距隨關卡可能變小，增加難度
            min_distance = max(80 - self.current_level*2, 50)
            overlap = any((x-ox)**2 + (y-oy)**2 < min_distance**2 for ox,oy in positions)
            if not overlap:
                positions.append((x,y))
                action = random.choice(["short","long"])
                cid = self.canvas.create_oval(x-40,y-40,x+40,y+40,outline="black",width=2)
                tid = self.canvas.create_text(x,y,text="短按" if action=="short" else "長按",font=("Arial",12))
                self.current_circles.append({
                    "id": cid, "text_id": tid, "x": x, "y": y,
                    "action": action, "pressed_time": None, "done": False
                })
                generated += 1
            attempts += 1
        
        # 隨關卡增加長按判定難度
        self.min_longpress_time = 0.8 + (self.current_level-1)*0.1
    
    # ------------------- 點擊與長按 -------------------
    def mouse_click(self, event):
        self.start_time = time.time()
        self.check_circle(event.x,event.y,"press")
    def mouse_release(self, event):
        end_time = time.time()
        self.check_circle(event.x,event.y,"release",end_time)
        self.check_level_complete()
    def check_circle(self, x, y, event_type, release_time=None):
        for circle in self.current_circles:
            if circle["done"]: continue
            cx,cy = circle["x"],circle["y"]
            if (x-cx)**2 + (y-cy)**2 <= 40**2:
                if event_type=="press":
                    circle["pressed_time"]=time.time()
                    self.animate_circle(cx,cy,expanding=True)
                elif event_type=="release":
                    duration = release_time - circle["pressed_time"]
                    correct=False
                    if circle["action"]=="short" and duration<self.min_longpress_time:
                        correct=True
                    elif circle["action"]=="long" and duration>=self.min_longpress_time:
                        correct=True
                    circle["done"]=True
                    color = "green" if correct else "red"
                    self.canvas.itemconfig(circle["id"],outline=color,width=3)
    
    # ------------------- 關卡檢測 -------------------
    def check_level_complete(self):
        if all(c["done"] for c in self.current_circles):
            self.current_level += 1
            self.root.after(1000,self.start_level)
    
    # ------------------- 點擊動畫 -------------------
    def animate_circle(self,x,y,expanding=True,steps=10):
        start_radius = 5 if expanding else 50
        end_radius = 50 if expanding else 5
        circle = self.canvas.create_oval(x-start_radius,y-start_radius,x+start_radius,y+start_radius,outline="red",width=2)
        delta = (end_radius - start_radius)/steps
        def step(i=0):
            if i>=steps: 
                self.canvas.delete(circle)
                return
            new_radius = start_radius + delta*(i+1)
            self.canvas.coords(circle,x-new_radius,y-new_radius,x+new_radius,y+new_radius)
            color_value = int(255-(i/steps)*200)
            color_value=max(0,color_value)
            color_hex=f'#{color_value:02x}0000'
            self.canvas.itemconfig(circle,outline=color_hex)
            self.root.after(30,lambda: step(i+1))
        step()
    
    # ------------------- 開發版打包功能 -------------------
    def pack_game(self):
        py_file = os.path.abspath(__file__)
        exe_name = "TouchTestGame"
        try:
            import PyInstaller
        except ImportError:
            try:
                subprocess.check_call([sys.executable,"-m","pip","install","pyinstaller"])
                messagebox.showinfo("安裝完成","PyInstaller 已自動安裝完成！")
            except Exception as e:
                messagebox.showerror("安裝失敗",f"自動安裝 PyInstaller 失敗: {e}")
                return
        cmd = f'{sys.executable} -m PyInstaller --onefile --windowed --name "{exe_name}" "{py_file}"'
        try:
            subprocess.run(cmd,check=True,shell=True)
            messagebox.showinfo("完成",f"已生成 EXE，請查看 dist 資料夾中的 {exe_name}.exe")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("打包失敗",f"打包失敗: {e}")

# ------------------- 執行 -------------------
if __name__=="__main__":
    root=tk.Tk()
    app=TouchTestGame(root)
    root.mainloop()
