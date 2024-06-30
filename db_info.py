import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import os
import sys

   
   
   
file_path = os.path.abspath('connection_data.txt')

host = None
user = None
password = None
db_name = None
data = None
schema_entry = None

# Main window
root = tk.Tk()
root.geometry("1920x1080+400+150")
root.resizable(width=True, height=True)
root.title("DBKIS_Info")
root.withdraw() 


def save_connection_data(host, user, password, db_name, schema_name):
    if getattr(sys, 'frozen', False):  
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)  

    file_path = os.path.join(base_path, 'connection_data.txt')
    with open(file_path, 'w') as file:
        file.write(f"{host}\n{user}\n{password}\n{db_name}\n{schema_name}")


def load_connection_data():
    if getattr(sys, 'frozen', False):  
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__) 

    file_path = os.path.join(base_path, 'connection_data.txt')
    try:
        with open(file_path, 'r') as file:
            host = file.readline().strip()
            user = file.readline().strip()
            password = file.readline().strip()
            db_name = file.readline().strip()
            schema_name = file.readline().strip()
            return host, user, password, db_name, schema_name
    except FileNotFoundError:
        return None, None, None, None, None


def show_connection_window():
    def connect():
        global host, user, password, db_name,schema_entry
        host = host_entry.get()
        user = user_entry.get()
        password = password_entry.get()
        db_name = db_name_entry.get()
        schema_entry = schema_name_entry.get()
        save_connection_data(host, user, password, db_name, schema_entry)
        try:
            conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host)
            conn.close()  
            connection_window.destroy()
            root.deiconify() 
            fetch_data() 
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных: {e}")

    host, user, password, db_name, schema_entry = load_connection_data()

    connection_window = tk.Toplevel(root)
    connection_window.title("Введите данные подключения")
    connection_window.geometry("450x380+700+500")

    connection_window.config (background= "#D8DEE9")

    tk.Label(connection_window, text="Хост:", font=('Arial', 15, 'bold'), background= "#D8DEE9").pack()
    host_entry = tk.Entry(connection_window, width=30, font=('Arial', 18), background="#ECEFF4")
    host_entry.pack()
    host_entry.insert(0, host)
    tk.Label(connection_window, text="Имя пользователя:", font=('Arial', 15, 'bold'), background= "#D8DEE9").pack()
    user_entry = tk.Entry(connection_window, width=30, font=('Arial', 18), background="#ECEFF4")  
    user_entry.pack()
    user_entry.insert(0, user)

    tk.Label(connection_window, text="Пароль:", font=('Arial', 15, 'bold'), background= "#D8DEE9").pack()
    password_entry = tk.Entry(connection_window, show="*", width=30, font=('Arial', 18), background="#ECEFF4") 
    password_entry.pack()
    password_entry.insert(0, password)

    tk.Label(connection_window, text="Имя базы данных:", font=('Arial', 15, 'bold'), background= "#D8DEE9").pack()
    db_name_entry = tk.Entry(connection_window, width=30, font=('Arial', 18), background="#ECEFF4") 
    db_name_entry.pack()
    db_name_entry.insert(0, db_name)

    tk.Label(connection_window, text="Схема:", font=('Arial', 15, 'bold'), background="#D8DEE9").pack()
    schema_name_entry = tk.Entry(connection_window, width=30, font=('Arial', 18), background="#ECEFF4")
    schema_name_entry.pack()
    schema_name_entry.insert(0, schema_entry)

    connect_button = tk.Button(connection_window, text="Подключиться", font=('Arial', 20),background='#A3BE8C', command=connect)
    connect_button.pack()

show_connection_window()


# Cursor
def fetch_data():
    global data
    try:
        conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host)
        cursor = conn.cursor()
        cursor.execute("""
        WITH QUERY AS (
            SELECT n.nspname AS schemaname, c.relname AS tablename, OBJ_DESCRIPTION(c.oid) AS description, c.reltuples 
            FROM pg_class c
            LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_tablespace t ON t.oid = c.reltablespace
            WHERE (c.relkind = 'r'::CHAR OR c.relkind = 'f'::CHAR) AND n.nspname =  %s
        )
        SELECT CONCAT_WS('          ', col.table_schema || '.' || col.table_name, query.description) AS table_name,
               col.column_name,
               CONCAT_WS(' ', col.data_type, '[' || col.character_maximum_length || ']') AS col_type,
               col.is_nullable,
               COL_DESCRIPTION(c.oid, col.ordinal_position) AS comment
        FROM information_schema.columns col
        INNER JOIN QUERY ON QUERY.schemaname = col.table_schema AND QUERY.tablename = col.table_name
        LEFT JOIN pg_namespace ns ON ns.nspname = col.table_schema
        LEFT JOIN pg_class c ON col.table_name = c.relname AND c.relnamespace = ns.oid
        ORDER BY col.table_schema, col.table_name, col.ordinal_position;
    """, (schema_entry,)) 
        data = cursor.fetchall()
        display_data(data, tree)
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")

# Fill treeview
def display_data(data, tree):
    tree.delete(*tree.get_children()) 
    for row in data:
        last = tree.insert('', 'end', text=row[0])
        for i, col in enumerate(row[1:]):
            tree.set(last, i+1, col)


def search_data():
    global data
    search_text = search_entry.get().lower()
    filtered_data = [row for row in data if search_text in ' '.join(col for col in row if col is not None).lower()]
    display_data(filtered_data, tree)

# Auto search
def search_on_key_release(event):
    search_data()


def display_data(data,tree):
    tree.delete(*tree.get_children()) 
    for row in data:
        last = tree.insert('', 'end', text=row[0])
        for i, col in enumerate(row[0:]):
            tree.set(last, i, col)
    pass


label_side = tk.Label(root, text="Рядовой А. А., 2024г.", bg="#D8DEE9")
label_side.pack(side=tk.TOP, anchor=tk.E, padx=5, pady=5)

#Styles
style = ttk.Style(root)
style.theme_use("clam") 

style.configure("Treeview", background="#D8E1E8", foreground="black", font=('Arial', 11))
style.configure("Treeview.Heading", font=("Arial", 15, "bold"), foreground="black", background="#D8DEE9")
style.configure("Treeview", justify="center")

column_names = ['table_name', 'column_name', 'col_type', 'is_nullable', 'comment']
tree = ttk.Treeview(root, columns=column_names, show='headings')

tree.column('table_name', width=600)
tree.column('column_name', width=300)
tree.column('col_type', width=300)
tree.column('is_nullable', width=120)
tree.column('comment', width=1000)

for i, col in enumerate(column_names):
    tree.heading(col, text=col.title())

tree.heading('table_name', text='Имя таблицы в БД')
tree.heading('column_name', text='Имя столбца в БД')
tree.heading('is_nullable', text='Nullable?')
tree.heading('comment', text='Комментарий')

# Scrollbar Х
scrollbar_x = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
tree.config(xscrollcommand=scrollbar_x.set)
scrollbar_x.pack(side="bottom", fill="x")

# Scrollbar Y
scrollbar_y = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.config(yscrollcommand=scrollbar_y.set)
scrollbar_y.pack(side="right", fill="y")

#Search
search_frame = tk.Frame(root)
search_frame.pack(fill='x')
search_entry = tk.Entry(search_frame, width=25, font=("Arial", 18),background="#A3BE8C")
search_entry.pack(side='right', fill='x', expand=True)
search_button = tk.Label(search_frame, text="Поиск >>", width=25, height=2, background="#EBCB8B")
search_button.pack(side='right')

#Search entry 
search_entry.bind("<KeyRelease>", lambda event: search_on_key_release(event))

tree.pack(fill="both", expand=True)


root.mainloop()