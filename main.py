import tkinter as tk
from tkinter import ttk, messagebox
import bcrypt
from database import get_session
from models import User, Member, FinancialTransaction, AuditLog

class YetuSaccoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yetu SACCO Management System")
        self.geometry("900x600")
        
        self.current_user = None
        self.session = get_session()

        # Container to stack frames
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        # Initialize pages
        for F in (LoginFrame, DashboardFrame, MembersFrame, TransactionsFrame):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Yetu SACCO Login", font=("Helvetica", 18, "bold")).pack(pady=40)

        tk.Label(self, text="Username").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Password").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Login", command=self.attempt_login, bg="blue", fg="white").pack(pady=20)

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get().encode('utf-8')
        
        user = self.controller.session.query(User).filter_by(username=username).first()
        
        if user and bcrypt.checkpw(password, user.password_hash.encode('utf-8')):
            self.controller.current_user = user
            self.controller.show_frame("DashboardFrame")
        else:
            messagebox.showerror("Error", "Invalid username or password")

class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.header = tk.Label(self, text="Dashboard", font=("Helvetica", 16, "bold"))
        self.header.pack(pady=20)
        
        self.stats_frame = tk.Frame(self)
        self.stats_frame.pack(fill="x", padx=20)
        
        # Logout button
        tk.Button(self, text="Logout", command=self.logout).pack(pady=20)

    def on_show(self):
        # Refresh data when frame is raised
        self.header.config(text=f"Welcome, {self.controller.current_user.username}")
        # Here you would run session queries for total_members, total_savings, etc.

        tk.Button(self, text="View Member Directory", command=lambda: self.controller.show_frame("MembersFrame"), bg="gray", fg="white").pack(pady=10)
        tk.Button(self, text="Manage Transactions", command=lambda: self.controller.show_frame("TransactionsFrame"), bg="blue", fg="white").pack(pady=5)

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame("LoginFrame")

class MembersFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=10, padx=20)
        tk.Label(header_frame, text="Member Directory", font=("Helvetica", 16, "bold")).pack(side="left")
        tk.Button(header_frame, text="Back to Dashboard", command=lambda: self.controller.show_frame("DashboardFrame")).pack(side="right")
        
        # Treeview Container (to hold the tree and scrollbar)
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")
        
        # Define Columns
        columns = ("no", "name", "id", "savings", "active_loans")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        # Define Headings matching the original HTML table structure
        self.tree.heading("no", text="No")
        self.tree.heading("name", text="Name")
        self.tree.heading("id", text="National ID")
        self.tree.heading("savings", text="Savings (KES)")
        self.tree.heading("active_loans", text="Active Loans (KES)")
        
        # Format Columns
        self.tree.column("no", width=80, anchor="center")
        self.tree.column("name", width=200, anchor="w")
        self.tree.column("id", width=120, anchor="center")
        self.tree.column("savings", width=150, anchor="e")
        self.tree.column("active_loans", width=150, anchor="e")

    def on_show(self):
        # Clear existing data before populating
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Fetch active members using the centralized session
        from models import Member # Local import to avoid circular dependency if models are separated
        members = self.controller.session.query(Member).filter_by(is_active=True).all()
        
        # Insert rows into Treeview
        for m in members:
            # Safely handle None values if calculations return empty
            savings_val = m.total_savings if m.total_savings else 0.00
            loans_val = m.active_loans_total if m.active_loans_total else 0.00
            
            self.tree.insert("", tk.END, values=(
                m.member_no,
                m.full_name,
                m.national_id,
                f"{savings_val:,.2f}",
                f"{loans_val:,.2f}"
            ))

class TransactionsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=10, padx=20)
        tk.Label(header_frame, text="Record Transaction", font=("Helvetica", 16, "bold")).pack(side="left")
        tk.Button(header_frame, text="Back to Dashboard", command=lambda: self.controller.show_frame("DashboardFrame")).pack(side="right")
        
        content_frame = tk.Frame(self)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Form Container (Left Side)
        form_frame = tk.Frame(content_frame, width=300)
        form_frame.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(form_frame, text="Select Member:").pack(anchor="w")
        self.member_var = tk.StringVar()
        self.member_dropdown = ttk.Combobox(form_frame, textvariable=self.member_var, state="readonly")
        self.member_dropdown.pack(fill="x", pady=(0, 10))
        
        tk.Label(form_frame, text="Transaction Type:").pack(anchor="w")
        self.type_var = tk.StringVar(value="Savings")
        ttk.Combobox(form_frame, textvariable=self.type_var, values=["Savings", "Withdrawal", "Share Capital"], state="readonly").pack(fill="x", pady=(0, 10))
        
        tk.Label(form_frame, text="Amount (KES):").pack(anchor="w")
        self.amount_entry = tk.Entry(form_frame)
        self.amount_entry.pack(fill="x", pady=(0, 10))
        
        tk.Button(form_frame, text="Submit Transaction", bg="green", fg="white", command=self.process_transaction).pack(fill="x", pady=10)

        # Ledger Container (Right Side)
        ledger_frame = tk.Frame(content_frame)
        ledger_frame.pack(side="right", fill="both", expand=True)
        
        columns = ("date", "member", "amount", "type")
        self.tree = ttk.Treeview(ledger_frame, columns=columns, show="headings")
        self.tree.heading("date", text="Date")
        self.tree.heading("member", text="Member")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("type", text="Type")
        self.tree.pack(fill="both", expand=True)

    def on_show(self):
        # Populate Member Dropdown
        members = self.controller.session.query(Member).filter_by(is_active=True).all()
        self.member_map = {f"{m.member_no} - {m.full_name}": m.id for m in members}
        self.member_dropdown['values'] = list(self.member_map.keys())
        
        self.refresh_ledger()

    def refresh_ledger(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        txs = self.controller.session.query(FinancialTransaction).order_by(FinancialTransaction.date.desc()).limit(20).all()
        for t in txs:
            member_name = t.member.full_name if t.member else "Unknown"
            self.tree.insert("", tk.END, values=(t.date.strftime('%Y-%m-%d %H:%M'), member_name, f"KES {t.amount:,.2f}", t.transaction_type))

    def process_transaction(self):
        selection = self.member_var.get()
        if not selection:
            messagebox.showwarning("Input Error", "Please select a member.")
            return
            
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Amount must be a number.")
            return

        member_id = self.member_map[selection]
        tx_type = self.type_var.get()
        member = self.controller.session.query(Member).get(member_id)
        
        # Enforce Withdrawal Overdraft Rule
        if tx_type == 'Withdrawal' and amount > member.total_savings:
            messagebox.showerror("Denied", f"Insufficient savings. Available balance: KES {member.total_savings:,.2f}")
            return
            
        # Record Transaction
        tx = FinancialTransaction(member_id=member_id, transaction_type=tx_type, amount=amount)
        self.controller.session.add(tx)
        
        # Audit Log
        log = AuditLog(user_id=self.controller.current_user.id, action=f"Recorded {tx_type} of {amount} for {member.member_no}")
        self.controller.session.add(log)
        
        self.controller.session.commit()
        messagebox.showinfo("Success", "Transaction recorded successfully.")
        self.amount_entry.delete(0, tk.END)
        self.refresh_ledger()

if __name__ == "__main__":
    app = YetuSaccoApp()
    app.mainloop()