import tkinter as tk
from tkinter import ttk
import psycopg2
from config import host, user, password, db_name



# Main window
root = tk.Tk()
root.geometry("1920x1080+400+150")
root.resizable(width=True, height=True)
root.title("DBKIS_Info")
root["bg"] = '#9BC1BC'


# Connecting PG
try:
    conn = psycopg2.connect(dbname=db_name, user=user, password=password, host=host)
    cursor = conn.cursor()
except Exception as e:
    print(e)
    root.destroy()

# Query to get column names
def get_column_names(cursor):
    cursor.execute("""
        WITH QUERY AS (
            SELECT n.nspname AS schemaname, c.relname AS tablename, OBJ_DESCRIPTION(c.oid) AS description, c.reltuples 
            FROM pg_class c
            LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
            LEFT JOIN pg_tablespace t ON t.oid = c.reltablespace
            WHERE (c.relkind = 'r'::CHAR OR c.relkind = 'f'::CHAR) AND n.nspname = 'mm'
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
    """)
    return [desc[0] for desc in cursor.description]

# Fill treeview
def fill_treeview(tree, data):
    tree.delete(*tree.get_children()) 
    for row in data:
        last = tree.insert('', 'end', text=row[0])
        for i, col in enumerate(row[0:]):
            tree.set(last, i, col)


def search_data():
    search_text = search_entry.get().lower()
    filtered_data = [row for row in data if search_text in ' '.join(col for col in row if col is not None).lower()]
    fill_treeview(tree, filtered_data)

# Auto search
def search_on_key_release(event):
    search_data()


column_names = get_column_names(cursor)

#Style for columns and Treeview

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
search_button = tk.Label(search_frame, text="Поиск >", width=25, height=2, background="#EBCB8B")
search_button.pack(side='right')

#Search entry 
search_entry.bind("<KeyRelease>", search_on_key_release)


data = cursor.fetchall()

search_data()

tree.pack(fill="both", expand=True)

root.mainloop()
