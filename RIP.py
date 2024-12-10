import time
import copy
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class Router:
    def __init__(self, name):
        self.name = name
        self.routing_table = {name: {"cost": 0, "next_hop": name}}  # Initial routing table

    def update_routing_table(self, neighbor_table, neighbor, link_cost):
        updated = False
        for dest, info in neighbor_table.items():
            new_cost = info["cost"] + link_cost
            if dest not in self.routing_table or new_cost < self.routing_table[dest]["cost"]:
                self.routing_table[dest] = {"cost": new_cost, "next_hop": neighbor}
                updated = True
        return updated

class Network:
    def __init__(self):
        self.routers = {}
        self.links = {}

    def add_router(self, name):
        self.routers[name] = Router(name)

    def connect_routers(self, router1, router2, cost):
        self.links.setdefault(router1, {})[router2] = cost
        self.links.setdefault(router2, {})[router1] = cost

    def simulate_rip(self, update_ui):
        converged = False
        while not converged:
            converged = True
            for router_name, router in self.routers.items():
                for neighbor, cost in self.links.get(router_name, {}).items():
                    neighbor_table = self.routers[neighbor].routing_table
                    if router.update_routing_table(neighbor_table, neighbor, cost):
                        converged = False
            update_ui()  # Update the UI with the latest routing tables
            time.sleep(1)  # Simulate periodic updates

class RIPSimulatorUI:
    def __init__(self, root):
        self.root = root
        self.network = Network()

        self.root.title("RIP Simulation")
        self.root.geometry("800x600")
        self.root.configure(bg="#f4f4f4")

        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=5)
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TEntry", font=("Helvetica", 12))

        self.router_frame = ttk.Frame(self.root)
        self.router_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(self.router_frame, text="Router Name:").pack(side=tk.LEFT)
        self.router_name_entry = ttk.Entry(self.router_frame)
        self.router_name_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.router_frame, text="Add Router", command=self.add_router).pack(side=tk.LEFT, padx=5)

        self.link_frame = ttk.Frame(self.root)
        self.link_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(self.link_frame, text="Router 1:").pack(side=tk.LEFT)
        self.link_router1_entry = ttk.Entry(self.link_frame)
        self.link_router1_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.link_frame, text="Router 2:").pack(side=tk.LEFT)
        self.link_router2_entry = ttk.Entry(self.link_frame)
        self.link_router2_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.link_frame, text="Cost:").pack(side=tk.LEFT)
        self.link_cost_entry = ttk.Entry(self.link_frame)
        self.link_cost_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(self.link_frame, text="Connect Routers", command=self.connect_routers).pack(side=tk.LEFT, padx=5)

        ttk.Button(self.root, text="Simulate RIP", command=self.simulate_rip).pack(pady=10)
        ttk.Button(self.root, text="View Routers & Paths", command=self.view_routers_paths).pack(pady=5)

        self.output_text = tk.Text(self.root, state=tk.DISABLED, height=20, font=("Courier", 10))
        self.output_text.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)

    def add_router(self):
        router_name = self.router_name_entry.get().strip()
        if router_name:
            self.network.add_router(router_name)
            messagebox.showinfo("Success", f"Router {router_name} added.")
            self.router_name_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "Please enter a router name.")

    def connect_routers(self):
        router1 = self.link_router1_entry.get().strip()
        router2 = self.link_router2_entry.get().strip()
        try:
            cost = int(self.link_cost_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid cost.")
            return

        if router1 and router2 and cost > 0:
            if router1 in self.network.routers and router2 in self.network.routers:
                self.network.connect_routers(router1, router2, cost)
                messagebox.showinfo("Success", f"Connected {router1} and {router2} with cost {cost}.")
                self.link_router1_entry.delete(0, tk.END)
                self.link_router2_entry.delete(0, tk.END)
                self.link_cost_entry.delete(0, tk.END)
            else:
                messagebox.showwarning("Error", "Both routers must exist.")
        else:
            messagebox.showwarning("Input Error", "Please fill in all fields correctly.")

    def simulate_rip(self):
        def update_ui():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "\nRouting Tables:\n")
            for router_name, router in self.network.routers.items():
                self.output_text.insert(tk.END, f"Router {router_name}:\n")
                for dest, info in router.routing_table.items():
                    self.output_text.insert(
                        tk.END, f"  To {dest}: cost={info['cost']}, next_hop={info['next_hop']}\n"
                    )
            self.output_text.config(state=tk.DISABLED)

        threading.Thread(target=self.network.simulate_rip, args=(update_ui,), daemon=True).start()

    def view_routers_paths(self):
        paths_info = "Network Paths:\n"
        for router_name, links in self.network.links.items():
            for neighbor, cost in links.items():
                paths_info += f"{router_name} -> {neighbor} : cost={cost}\n"

        messagebox.showinfo("Routers & Paths", paths_info)

if __name__ == "__main__":
    root = tk.Tk()
    app = RIPSimulatorUI(root)
    root.mainloop()
