import os
import platform
import subprocess
import threading
from tkinter import ttk, messagebox, Tk, LEFT, Y, X, BooleanVar, HORIZONTAL, StringVar, BOTTOM, BOTH, RIGHT, NORMAL, DISABLED, DoubleVar
import matplotlib.pyplot as plt
import pandas as pd
import  psutil
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

monitor_after_id = None

def get_cpu_name():
    try:
        import cpuinfo
        return cpuinfo.get_cpu_info()['brand_raw']
    except ImportError:
        return "cpuinfo not installed"
    except Exception:
        return "Unknown CPU"


cpu_name = get_cpu_name()
os_details = f"{platform.system()} {platform.release()} {platform.machine()}"
last_disk_io = psutil.disk_io_counters()

def update_monitor():
    global last_disk_io, monitor_after_id
    try:
        cpu_usage = psutil.cpu_percent()
        var_cpu.set(cpu_usage)
        if cpu_usage < 50:
            cpu_color = "green"
        else:
            if cpu_usage > 50 and cpu_usage < 75:
                cpu_color = "orange"
            else:
                cpu_color = "red"

        lbl_cpu_val.config(text=f"{cpu_usage}%", foreground=cpu_color)

        mem = psutil.virtual_memory()
        var_ram.set(mem.percent)
        gb_used = mem.used / 1024 / 1024 / 1024
        gb_total = mem.total / 1024 / 1024 / 1024


        if mem.percent < 50:
            ram_color = "green"
        else:
            if mem.percent > 50 and mem.percent < 75:
                ram_color = "orange"
            else:
                ram_color = "red"
        lbl_ram_val.config(text=f"{mem.percent}% ({gb_used:.1f} GB / {gb_total:.1f} GB)", foreground=ram_color)

        current_disk_io = psutil.disk_io_counters()

        read_dif = current_disk_io.read_bytes - last_disk_io.read_bytes
        write_dif = current_disk_io.write_bytes - last_disk_io.write_bytes
        total_bytes_mb_sec = (read_dif + write_dif) / 1024 / 1024

        disk_percent = min(total_bytes_mb_sec, 100)
        var_disk.set(disk_percent)

        if disk_percent < 50:
            disk_color = "green"
        else:
            if disk_percent > 50 and disk_percent < 75:
                disk_color = "orange"
            else:
                disk_color = "red"

        if total_bytes_mb_sec > 0.1:
            lbl_disk_val.config(text=f"{total_bytes_mb_sec:.1f} MB/s (Activ)", foreground=disk_color)
        else:
            lbl_disk_val.config(text="0.0 MB/s (inactiv)", foreground="black")

        last_disk_io = current_disk_io

        monitor_after_id = root.after(1000, update_monitor)
    except:
        pass

def on_closing():

    if monitor_after_id:
        root.after_cancel(monitor_after_id)
    root.destroy()


def run_benchmark_thread():
    try:
        limit_mb = int(var_limit.get().split()[0])
        limit_bytes = limit_mb * 1024 * 1024

        f_seq = 1 if var_seq.get() else 0
        f_ran = 1 if var_ran.get() else 0
        f_row = 1 if var_row.get() else 0
        f_col = 1 if var_col.get() else 0
        f_frag = 1 if var_frag.get() else 0

        if (f_seq + f_ran + f_row + f_col + f_frag) == 0:
            messagebox.showwarning("Atentie", "Selecteaza cel putin un tip de test!")
            btn_run.config(state=NORMAL)
            return

        cmd = ["bin/Debug/proiect.exe", str(limit_bytes), str(f_seq), str(f_ran), str(f_row), str(f_col), str(f_frag)]

        if not os.path.exists("bin/Debug/proiect.exe"):
            messagebox.showerror("Eroare", "Lipseste proiect.exe! Compileaza codul C.")
            return

        lbl_status.config(text=f"Status: Rulare teste pana la {limit_mb} MB", foreground="green")
        root.update()

        pt.clear()
        pt.set_title("Testare in curs.")
        pt.set_xlabel("")
        pt.set_ylabel("")
        pt.set_xscale("log")
        pt.grid(True)
        canvas.draw()

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line.startswith("STARE:"):
                    msg = line.replace("STARE:", "").strip()
                    lbl_status.config(text=msg, foreground="blue")
                else:
                    lbl_status.config(text="", foreground="red")
        return_code = process.wait()
        if return_code == 0:
            lbl_status.config(text="Status: Finalizat! Se genereaza graficul", foreground="blue")
            root.after(100, draw_graph)
        else:
            lbl_status.config(text="Eroare in codul C", foreground="red")
            messagebox.showerror("Eroare C", process.stderr)

    except Exception as e:
        messagebox.showerror("Eroare", str(e))
    finally:
        btn_run.config(state=NORMAL)


def start_test():
    btn_run.config(state=DISABLED)
    threading.Thread(target=run_benchmark_thread, daemon=True).start()


def draw_graph():
    try:
        if not os.path.exists("rezultate.csv"):
            return
        df = pd.read_csv("rezultate.csv")
        if df.empty:
            messagebox.showinfo("Info", "Fisierul CSV este gol")
            return
        df["Dim_MB"] = df["Dimensiune(bytes)"] / (1024 * 1024)
        tipuri = df["Tip"].unique()

        pt.clear()

        for tip in tipuri:
            subset = df[df["Tip"] == tip]
            pt.plot(subset["Dim_MB"], subset["Viteza(MB/s)"], marker="o", label=tip)

        pt.set_title("Viteza de transfer in functie de dimensiunea datelor")
        pt.set_xlabel("Dimensiune accesata (MB)")
        pt.set_ylabel("Viteza (MB/s)")
        pt.set_xscale("log")
        pt.grid(True, which="both", ls="-", alpha=0.5)
        pt.legend()

        canvas.draw()


    except Exception as e:
        lbl_status.config(text=f"Eroare grafic: {e}", foreground="red")

root = Tk()
root.title("Program de testare a performantelor de transfer pentru memoriile cache ")
root.geometry("1100x900")

var_cpu = DoubleVar()
var_ram = DoubleVar()
var_disk = DoubleVar()

frame_left = ttk.Frame(root, padding=15)
frame_left.pack(side=LEFT, fill=Y)

sys_info = ttk.LabelFrame(frame_left, text="Informatii sistem", padding=10)
sys_info.pack(fill=X, pady=5)
ttk.Label(sys_info, text=f"CPU: {cpu_name}").pack(anchor="w")
ttk.Label(sys_info, text=f"OS: {os_details}").pack(anchor="w")

data_frame = ttk.LabelFrame(frame_left, text="Monitorizare live", padding=10)
data_frame.pack(fill=X, pady=10)

ttk.Label(data_frame, text="Utilizare CPU:").pack(anchor="w")
prb_cpu = ttk.Progressbar(data_frame, variable=var_cpu, maximum=100)
prb_cpu.pack(fill=X, pady=(0, 2))
lbl_cpu_val = ttk.Label(data_frame, text="0%")
lbl_cpu_val.pack(anchor="w")

ttk.Label(data_frame, text="Utilizare RAM:").pack(anchor="w")
prb_ram = ttk.Progressbar(data_frame, variable=var_ram, maximum=100)
prb_ram.pack(fill=X, pady=(0, 2))
lbl_ram_val = ttk.Label(data_frame, text="0 GB")
lbl_ram_val.pack(anchor="w")

ttk.Label(data_frame, text="Activitate DISK:").pack(anchor="w")
prb_disk = ttk.Progressbar(data_frame, variable=var_disk, maximum=100)
prb_disk.pack(fill=X, pady=(0, 2))
lbl_disk_val = ttk.Label(data_frame, text="0 MB/s")
lbl_disk_val.pack(anchor="w")


tests_type = ttk.LabelFrame(frame_left, text="Selectie teste", padding=10)
tests_type.pack(fill=X, pady=10)

var_seq = BooleanVar(value=True)
var_ran = BooleanVar(value=True)
var_row = BooleanVar(value=False)
var_col = BooleanVar(value=False)
var_frag = BooleanVar(value=False)

ttk.Checkbutton(tests_type, text="Acces Secvential", variable=var_seq).pack(anchor="w")
ttk.Checkbutton(tests_type, text="Acces Aleatoriu", variable=var_ran).pack(anchor="w")
ttk.Separator(tests_type, orient=HORIZONTAL).pack(fill=X, pady=5)
ttk.Checkbutton(tests_type, text="Matrice - Linii", variable=var_row).pack(anchor="w")
ttk.Checkbutton(tests_type, text="Matrice - Coloane", variable=var_col).pack(anchor="w")
ttk.Checkbutton(tests_type, text="Matrice fragmentata", variable=var_frag).pack(anchor="w")

tests_size = ttk.LabelFrame(frame_left, text="Limita dimensiune", padding=10)
tests_size.pack(fill=X, pady=10)

ttk.Label(tests_size, text="Selecteaza dimensiunea maxima a testului:", wraplength=200).pack(anchor="w")
var_limit = StringVar(value="64 MB")
sizes=["16 MB", "64 MB", "256 MB", "1024 MB", "2048 MB", "4096 MB", "8192 MB"]
cmbox_size = ttk.Combobox(tests_size, textvariable=var_limit, values=sizes, state="readonly")
cmbox_size.pack(fill=X)

btn_run = ttk.Button(frame_left, text="START TESTE", command=start_test)
btn_run.pack(fill=X, pady=20)

lbl_status = ttk.Label(frame_left, text="Status: Asteptare...", wraplength=200)
lbl_status.pack(side=BOTTOM, pady=10)

frame_right = ttk.Frame(root, padding=10)
frame_right.pack(side=RIGHT, fill=BOTH, expand=True)

fig, pt = plt.subplots(figsize=(5, 4), dpi=100)

canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

update_monitor()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()