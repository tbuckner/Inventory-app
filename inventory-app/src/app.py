import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = Path("data/inventory.sqlite")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------- DB LAYER ----------------------
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = get_conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1
        )
    """)
    con.commit()
    con.close()

def add_item(name, location, qty):
    with get_conn() as con:
        con.execute(
            "INSERT INTO items(name, location, qty) VALUES (?,?,?)",
            (name, location, qty)
        )

def list_items():
    with get_conn() as con:
        return con.execute(
            "SELECT id, name, location, qty FROM items ORDER BY location, name"
        ).fetchall()

def update_item(item_id, name, location, qty):
    with get_conn() as con:
        con.execute(
            "UPDATE items SET name=?, location=?, qty=? WHERE id=?",
            (name, location, qty, item_id)
        )

def delete_item(item_id):
    with get_conn() as con:
        con.execute("DELETE FROM items WHERE id=?", (item_id,))

# ---------------------- UI HELPERS ----------------------
def clear_form():
    name_var.set("")
    loc_var.set("")
    qty_var.set("1")
    tree.selection_remove(tree.selection())

def refresh():
    # clear rows
    for iid in tree.get_children():
        tree.delete(iid)
    # reload
    for (iid, n, loc, q) in list_items():
        tree.insert("", "end", iid=str(iid), values=(n, loc, q))

def select_row(event=None):
    sel = tree.selection()
    if not sel:
        return
    iid = sel[0]
    vals = tree.item(iid, "values")
    # values: ("Name", "Location", "Qty")
    name_var.set(vals[0])
    loc_var.set(vals[1])
    qty_var.set(str(vals[2]))

def validate_inputs(require_selection=False):
    n = name_var.get().strip()
    l = loc_var.get().strip()
    q_raw = qty_var.get().strip()

    if require_selection:
        if not tree.selection():
            messagebox.showwarning("Select a row", "Please select an item first.")
            return None

    if not n or not l:
        messagebox.showerror("Missing info", "Name and Location are required.")
        return None

    try:
        q = int(q_raw)
        if q < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid quantity", "Quantity must be a non-negative integer.")
        return None

    return n, l, q

# ---------------------- BUTTON HANDLERS ----------------------
def on_add():
    vals = validate_inputs()
    if not vals:
        return
    n, l, q = vals
    add_item(n, l, q)
    clear_form()
    refresh()

def on_update():
    vals = validate_inputs(require_selection=True)
    if not vals:
        return
    n, l, q = vals
    sel = tree.selection()[0]
    item_id = int(sel)
    update_item(item_id, n, l, q)
    refresh()
    # keep selection on the same row if it still exists
    if tree.exists(str(item_id)):
        tree.selection_set(str(item_id))

def on_delete():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Select a row", "Please select an item to delete.")
        return
    item_id = int(sel[0])
    vals = tree.item(sel[0], "values")
    item_name = vals[0] if vals else "item"
    if not messagebox.askyesno("Confirm delete", f"Delete '{item_name}'?"):
        return
    delete_item(item_id)
    clear_form()
    refresh()

# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    init_db()

    root = tk.Tk()
    root.title("Inventory (MVP)")

    # Top frame: form + buttons
    frm = ttk.Frame(root, padding=10)
    frm.pack(fill="both", expand=True)

    name_var, loc_var, qty_var = tk.StringVar(), tk.StringVar(), tk.StringVar(value="1")

    # Form
    ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="w")
    ttk.Entry(frm, textvariable=name_var, width=24).grid(row=0, column=1, sticky="we")
    ttk.Label(frm, text="Location").grid(row=0, column=2, sticky="w")
    ttk.Entry(frm, textvariable=loc_var, width=16).grid(row=0, column=3, sticky="we")
    ttk.Label(frm, text="Qty").grid(row=0, column=4, sticky="w")
    ttk.Entry(frm, textvariable=qty_var, width=6).grid(row=0, column=5, sticky="we")

    # Buttons
    btns = ttk.Frame(frm)
    btns.grid(row=0, column=6, padx=6, sticky="e")
    ttk.Button(btns, text="Add", command=on_add).grid(row=0, column=0, padx=(0,4))
    ttk.Button(btns, text="Update", command=on_update).grid(row=0, column=1, padx=(0,4))
    ttk.Button(btns, text="Delete", command=on_delete).grid(row=0, column=2)

    # Tree (list)
    cols = ("Name", "Location", "Qty")
    tree = ttk.Treeview(frm, columns=cols, show="headings", height=14)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="w")
    tree.grid(row=1, column=0, columnspan=7, sticky="nsew", pady=(10,0))

    # Scrollbar
    yscroll = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=yscroll.set)
    yscroll.grid(row=1, column=7, sticky="ns", pady=(10,0))

    # Layout weights
    frm.columnconfigure(1, weight=1)
    frm.columnconfigure(3, weight=1)
    frm.rowconfigure(1, weight=1)

    # Bind selection
    tree.bind("<<TreeviewSelect>>", select_row)

    # Keyboard niceties
    root.bind("<Return>", lambda e: on_add())  # Enter to add (when nothing selected)
    # Ctrl+S to update if something is selected
    def try_update(e):
        if tree.selection():
            on_update()
    root.bind("<Control-s>", try_update)

    refresh()
    root.mainloop()
