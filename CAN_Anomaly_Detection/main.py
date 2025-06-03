from gui import CANAnomalyDetectorApp
import tkinter as tk

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1000x750")
    app = CANAnomalyDetectorApp(root)
    root.mainloop()