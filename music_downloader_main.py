#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from music_downloader_gui import MusicDownloaderGUI

def main():
    root = tk.Tk()
    try:
        root.iconbitmap('favicon.ico')
    except:
        pass
    app = MusicDownloaderGUI(root)
    
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()