# wiper_app.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import wiping_core
import certificate_generator

class WiperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Data Wiper")
        self.root.geometry("600x450")

        # --- UI Elements ---
        self.drive_frame = ttk.LabelFrame(root, text="Select Drive")
        self.drive_frame.pack(padx=10, pady=10, fill="x")

        self.drive_listbox = tk.Listbox(self.drive_frame, height=5)
        self.drive_listbox.pack(padx=5, pady=5, fill="x", expand=True)

        self.refresh_button = ttk.Button(self.drive_frame, text="Refresh Drives", command=self.populate_drives)
        self.refresh_button.pack(pady=5)

        self.method_frame = ttk.LabelFrame(root, text="Select Wiping Method")
        self.method_frame.pack(padx=10, pady=10, fill="x")
        self.wipe_method = tk.StringVar(value="overwrite")
        ttk.Radiobutton(self.method_frame, text="Secure Overwrite (3-Pass, NIST Clear)",
                        variable=self.wipe_method, value="overwrite").pack(anchor="w", padx=10)
        ttk.Radiobutton(self.method_frame, text="Hardware Secure Erase (NIST Purge - Advanced)",
                        variable=self.wipe_method, value="purge").pack(anchor="w", padx=10)

        self.progress_frame = ttk.LabelFrame(root, text="Progress")
        self.progress_frame.pack(padx=10, pady=10, fill="x")
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(pady=5, padx=10, fill="x")
        self.status_label = ttk.Label(self.progress_frame, text="Status: Ready")
        self.status_label.pack(pady=5, padx=10, anchor="w")

        self.wipe_button = ttk.Button(root, text="WIPE SELECTED DRIVE", command=self.confirm_and_wipe)
        self.wipe_button.pack(pady=20)

        self.drives = []
        self.populate_drives()

    def populate_drives(self):
        self.drive_listbox.delete(0, tk.END)
        self.status_label.config(text="Status: Detecting drives...")
        self.root.update_idletasks() # Ensure the UI updates
        self.drives = wiping_core.list_physical_drives()
        if not self.drives:
            self.drive_listbox.insert(tk.END, "No drives found or an error occurred.")
            self.drive_listbox.insert(tk.END, "Ensure 'util-linux' package is loaded.")
        else:
            for i, drive in enumerate(self.drives):
                display_text = f"{drive['path']} - {drive.get('model', 'N/A')} ({drive.get('size', 'N/A')})"
                self.drive_listbox.insert(tk.END, display_text)
        self.status_label.config(text="Status: Ready")

    def update_progress(self, message, value):
        self.status_label.config(text=f"Status: {message}")
        self.progress_bar['value'] = value
        self.root.update_idletasks()

    def confirm_and_wipe(self):
        try:
            selected_index = self.drive_listbox.curselection()[0]
            selected_drive = self.drives[selected_index]
        except IndexError:
            messagebox.showerror("Error", "Please select a drive to wipe.")
            return

        confirm1 = messagebox.askokcancel(
            "ARE YOU SURE?",
            f"You are about to permanently erase all data on:\n\n"
            f"{selected_drive['path']} ({selected_drive.get('model', 'N/A')})\n\n"
            "This action cannot be undone."
        )
        if not confirm1:
            return

        confirmation_text = "ERASE"
        user_input = simpledialog.askstring(
            "Final Confirmation",
            f"This is your final warning. To proceed, type '{confirmation_text}' in the box below."
        )

        if user_input != confirmation_text:
            messagebox.showwarning("Cancelled", "The wipe operation was cancelled.")
            return
        
        self.wipe_button.config(state="disabled")
        self.refresh_button.config(state="disabled")
        
        wipe_thread = threading.Thread(
            target=self.run_wipe_thread,
            args=(selected_drive, self.wipe_method.get())
        )
        wipe_thread.start()

    def run_wipe_thread(self, drive_info, method):
        """The actual work that runs in the background thread."""
        wipe_status = wiping_core.wipe_drive(drive_info['path'], method, self.update_progress)
        self.root.after(100, self.on_wipe_complete, wipe_status, drive_info, method)

    # ======================================================================
    # THIS IS THE CRITICAL CHANGE
    # ======================================================================
    def on_wipe_complete(self, wipe_status, drive_info, method):
        """Called on the main thread after the wipe is finished."""
        success, message = wipe_status

        # First, check if the wipe actually succeeded
        if not success:
            # If it failed, show an explicit error message and STOP.
            messagebox.showerror(
                "Wipe Failed!", 
                f"A critical error occurred during the wipe process:\n\n{message}"
            )
        else:
            # Only if it succeeded, generate the certificate and show success.
            self.update_progress("Generating certificate...", 100)
            json_path, pdf_path = certificate_generator.create_certificate(drive_info, method, wipe_status)
            messagebox.showinfo(
                "Success", 
                f"Wipe completed successfully.\n\nCertificate saved to:\n{json_path}\n{pdf_path}"
            )

        # Reset UI regardless of outcome
        self.progress_bar['value'] = 0
        self.status_label.config(text="Status: Ready")
        self.wipe_button.config(state="normal")
        self.refresh_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = WiperApp(root)
    root.mainloop()