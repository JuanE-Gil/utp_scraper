import json
from itsim import tkinter as tk
from itsim.tkinter import messagebox, ttk


DATA_FILE = "workday_tasks.json"
MAX_VISIBLE_TASKS = 5

default_tasks = [
    ["Revisar la cola de soporte", 25, False],
    ["Revisar informes de dispositivos", 35, False],
    ["Actualizar notas de servicio", 20, True],
]


def load_tasks():
    try:
        with open(DATA_FILE, "r") as data_file:
            loaded_tasks = json.load(data_file)

        if loaded_tasks:
            return loaded_tasks[:MAX_VISIBLE_TASKS]
    except Exception:
        pass

    return default_tasks


def save_tasks():
    with open(DATA_FILE, "w") as data_file:
        json.dump(tasks, data_file)


tasks = load_tasks()
task_buttons = []


def update_summary():
    completed = 0
    planned_minutes = 0

    for task in tasks:
        planned_minutes += task[1]
        if task[2]:
            completed += 1

    if tasks:
        progress_value.set(int(completed * 100 / len(tasks)))
    else:
        progress_value.set(0)

    completed_value.set(str(completed) + " / " + str(len(tasks)))
    minutes_value.set(str(planned_minutes) + " min")
    progress_text.set(str(progress_value.get()) + "% completado")


def create_toggle_command(index):
    def command():
        toggle_task(index)

    return command


def refresh_task_rows():
    global task_buttons

    for button in task_buttons:
        button.destroy()

    task_buttons = []

    for index in range(len(tasks)):
        text = ("[hecho] " if tasks[index][2] else "[ ] ") + tasks[index][0] + "  |  " + str(tasks[index][1]) + " min"
        button = tk.Button(
            left_card,
            text=text,
            command=create_toggle_command(index),
            bg="#17243a",
            fg="#e2e8f0"
        )
        button.place(x=18, y=132 + index * 48, width=500, height=40)
        task_buttons.append(button)

    update_summary()


def toggle_task(index):
    tasks[index][2] = not tasks[index][2]
    save_tasks()
    refresh_task_rows()


def add_task():
    name = task_name.get().strip()

    if not name:
        messagebox.showwarning("Planificador de la jornada", "Introduce primero un nombre de tarea.")
        return

    if len(tasks) >= MAX_VISIBLE_TASKS:
        messagebox.showwarning("Planificador de la jornada", "El plan diario puede contener hasta cinco tareas.")
        return

    tasks.append([name, 30, False])
    task_name.delete(0, tk.END)
    save_tasks()
    refresh_task_rows()


root = tk.Tk()
root.title("Planificador de la jornada")
root.geometry("860x560")
root.resizable(False, False)
root.configure(bg="#0b1220")

progress_value = tk.IntVar(value=0)
completed_value = tk.StringVar(value="0 / 3")
minutes_value = tk.StringVar(value="0 min")
progress_text = tk.StringVar(value="0% completado")

header = tk.Frame(root, bg="#111c31")
header.place(x=0, y=0, width=860, height=96)

tk.Label(header, text="WORKDAY PLANNER", bg="#111c31", fg="#67e8f9", font_size=13).place(x=34, y=20, width=210, height=24)
tk.Label(header, text="Organiza hoy. Termina con concentración.", bg="#111c31", fg="#f8fafc", font_size=24).place(x=34, y=45, width=470, height=34)
tk.Label(header, text="OPERACIONES DE TI", bg="#17334d", fg="#a5f3fc", font_size=11).place(x=680, y=31, width=142, height=34)

left_card = tk.Frame(root, bg="#111827")
left_card.place(x=14, y=108, width=536, height=394)

tk.Label(left_card, text="Plan de hoy", bg="#111827", fg="#f8fafc", font_size=20).place(x=18, y=14, width=210, height=34)
tk.Label(left_card, text="Mantén la cola despejada y al equipo informado.", bg="#111827", fg="#94a3b8", font_size=12).place(x=18, y=47, width=390, height=24)

task_name = ttk.Entry(left_card, width=300)
task_name.place(x=18, y=84, width=372, height=34)

ttk.Button(left_card, text="Añadir tarea", command=add_task).place(x=402, y=84, width=116, height=34)

tk.Label(left_card, text="Selecciona una fila para cambiar su estado.", bg="#111827", fg="#64748b", font_size=11).place(x=18, y=370, width=310, height=18)

right_card = tk.Frame(root, bg="#0f766e")
right_card.place(x=562, y=108, width=268, height=394)

tk.Label(right_card, text="HOY", bg="#0f766e", fg="#ccfbf1", font_size=12).place(x=22, y=22, width=90, height=24)
tk.Label(right_card, text="Progreso diario", bg="#0f766e", fg="#ffffff", font_size=22).place(x=22, y=52, width=190, height=34)

progress = ttk.Progressbar(right_card, maximum=100, variable=progress_value)
progress.place(x=22, y=105, width=224, height=18)
tk.Label(right_card, textvariable=progress_text, bg="#0f766e", fg="#ccfbf1", font_size=11).place(x=22, y=130, width=160, height=24)

tk.Label(right_card, text="Completado", bg="#0f766e", fg="#99f6e4", font_size=11).place(x=22, y=183, width=100, height=22)
tk.Label(right_card, textvariable=completed_value, bg="#0f766e", fg="#ffffff", font_size=22).place(x=22, y=206, width=150, height=34)

tk.Label(right_card, text="Tiempo planificado", bg="#0f766e", fg="#99f6e4", font_size=11).place(x=22, y=260, width=120, height=22)
tk.Label(right_card, textvariable=minutes_value, bg="#0f766e", fg="#ffffff", font_size=22).place(x=22, y=283, width=180, height=34)

ttk.Button(right_card, text="Cerrar planificador", command=root.destroy).place(x=22, y=338, width=224, height=36)

save_tasks()
refresh_task_rows()

with open("main.py", "r") as source_file:
    source_snapshot = source_file.read()

with open(".workday_planner_state.json", "w") as state_file:
    json.dump({"ready": True, "source": source_snapshot}, state_file)

root.mainloop()
