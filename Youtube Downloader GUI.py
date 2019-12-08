import tkinter as tk
import urllib.request
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk
import os
import youtube_dl
import concurrent.futures

# class creates an element. Display tumbnail, link and have a remove button
class Video:
    def __init__(self, l, f, v):
        self.info = Info(l)
        self.frame = tk.Frame(f, bg='#262626')
        self.frame.place(x=2, y=2+(v.index(self.info.url)*112), width=WIDTH-4, height=112)
        self.label = tk.Label(self.frame, bg='#303030', fg='white', bd=0, image=self.info.img)
        self.label.place(width=192, height=108, x=0, y=2)
        self.label = tk.Label(self.frame, text=str(self.info.title), bg='#363636', fg='#f6e080', bd=0)
        self.label.place(width=WIDTH-192-4-70, height=108, x=192, y=2)
        self.button = tk.Button(self.frame, text="Remove", bd=0, bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground ='#f6e080', command=lambda: RemoveFromList(self.info.url))
        self.button.place(width=70, height=108, x=WIDTH-74, y=2)

# info class to obatin all the details. i.e get the image and title
class Info:
    def __init__(self, link):
        self.url = link
        self.id = self.url[self.url.index('=')+1:]
        # get Title
        data = requests.get(self.url)
        soup = BeautifulSoup(data.text, 'html.parser')
        soup.prettify('utf-8')
        for span in soup.findAll('span', attrs={'class':'watch-title'}):
            self.title = span.text.strip()
        # get thumbnail
        if not os.path.isfile(str("./thumbnails/" + self.id + ".jpg")):
            self.imgURL = "http://i1.ytimg.com/vi/" + self.id + "/hqdefault.jpg"
            urllib.request.urlretrieve(self.imgURL, str("./thumbnails/" + self.id + ".jpg"))
        temp2 = Image.open(str("./thumbnails/" + self.id + ".jpg"))
        temp2 = temp2.resize((192,108), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(temp2)

# create vars
WIDTH = 1280
HEIGHT = 800
VIDEOLINKS = []

# create temp directory
dirName = 'thumbnails'
if not os.path.exists(dirName):
    os.mkdir(dirName)

# define functions
def AddToList(link):
    if link != "" and VIDEOLINKS.count(link) == 0:
        VIDEOLINKS.append(link)
        UpdateThreadHandler()
        i_link.delete(0,tk.END)

def UpdateThreadHandler():
    executor = concurrent.futures.ThreadPoolExecutor(1)
    futures = executor.submit(UpdateList, f_data, VIDEOLINKS)
        
def RemoveFromList(link):
    if link !="":
        VIDEOLINKS.pop(VIDEOLINKS.index(link))
        UpdateThreadHandler()

def UpdateList(f, v):
    for widget in f.winfo_children():
            widget.destroy()

    for i in v:
        Video(i, f, v)

def ClearList():
    VIDEOLINKS.clear()
    UpdateThreadHandler()

def DownloadList(opts, v, f):
    if len(v) > 0:
        for widget in f.winfo_children():
            widget.destroy()
        for i in v:
            with youtube_dl.YoutubeDL(opts) as ydl:
                ydl.download([i])
        ClearList()
        PrintToConsole("Merging/Converting Complete")

def DownloadThreadHandler(opts):
    PrintToConsole("Attempting to download...")
    executor = concurrent.futures.ThreadPoolExecutor(1)
    futures = executor.submit(DownloadList, opts, VIDEOLINKS, f_data)
    
def PrintToConsole(msg):
    t_command.configure(state=tk.NORMAL)
    t_command.insert(tk.END, msg + "\n")
    t_command.configure(state=tk.DISABLED)

def MyHook(d):
    if d['status'] == 'downloading':
        t_command.configure(state=tk.NORMAL)
        t_command.insert(tk.END, "[" + d['filename'] + "] " + d['_percent_str'] + "  ETA: " + d['_eta_str'] + "\n")
        t_command.configure(state=tk.DISABLED)

    if d['status'] == 'finished':
        t_command.configure(state=tk.NORMAL)
        t_command.insert(tk.END, "Download Complete\n")
        t_command.configure(state=tk.DISABLED)

def _bound_to_mousewheel(self, event):
    self.t_command.bind_all("<MouseWheel>", self._on_mousewheel)   

def _unbound_to_mousewheel(self, event):
    self.t_command.unbind_all("<MouseWheel>") 

def _on_mousewheel(self, event):
    self.t_command.yview_scroll(int(-1*(event.delta/120)), "units")

# option vars
opts_video = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'progress_hooks': [MyHook],
}

opts_audio = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'progress_hooks': [MyHook],
    'postprocessors': [
            {'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',
             'preferredquality': '192',
            },
            {'key': 'FFmpegMetadata'},
        ],
}

# setup window
window = tk.Tk()
window.resizable(False, False)
window.title( "Youtube Downloader GUI")

# Tkinter vars
OUTPUT = tk.StringVar()

# create buffer/canvas
buffer = tk.Canvas(window, height=HEIGHT, width=WIDTH, bg='black', highlightthickness=0)
buffer.pack()

# create layout
#  input frame
f_input = tk.Frame(buffer, bg='#262626', bd=0)
f_input.place(relx=0, rely=0, relwidth=1, height=28)

#  input funcitonal
l_search = tk.Label(f_input, font=('Arial', 8), text='Youtube Link:', bd=0, bg='#303030', fg='#f6e080' )
l_search.place(width=89, height=24, x=2, y=2)

i_link = tk.Entry(f_input, font=('Arial', 8), bd=0, relief='flat', bg='#363636', fg='white')
i_link.place(width=WIDTH-89-4-70, height=24, x=91, y=2)
i_link.focus_set()

b_add = tk.Button(f_input, text="Add", bd=0, bg='#303030', activebackground='#262626', fg='#f6e080', activeforeground='#f6e080', command=lambda: AddToList(i_link.get()))
b_add.place(width=70, height=24, x=WIDTH-72, y=2)

#  data frame
f_data = tk.Frame(buffer, bg='#202020', bd=0)
f_data.place(width=WIDTH, height=HEIGHT-28-26-204, x=0, y=HEIGHT-(HEIGHT-28))

# command output
#  command frame
f_command = tk.Frame(buffer, bg='#262626', bd=0)
f_command.place(width=WIDTH, height=204, x=0, y=HEIGHT-26-204)

#  command textbox
t_command = tk.Text(f_command, bg='#262626', bd=0, relief='flat', fg='#f6e080', width=WIDTH-4, state=tk.DISABLED)
t_command.pack(side='left', anchor='n')

# download
#  download frame
f_download = tk.Frame(buffer, bg='#262626', bd=0, relief='flat')
f_download.place(width=WIDTH, height=26, x=0, y=HEIGHT-26)

#  download button
b_download_video = tk.Button(f_download, text="Download Video/Audio", bd=0, bg='#303030', activebackground='#262626', fg='#f6e080', activeforeground='#f6e080', command=lambda: DownloadThreadHandler(opts_video))
b_download_video.place(width=WIDTH/2-3, height=24, x=2, y=2)

b_download_audio = tk.Button(f_download, text="Download Audio Only", bd=0, bg='#303030', activebackground='#262626', fg='#f6e080', activeforeground='#f6e080', command=lambda: DownloadThreadHandler(opts_audio))
b_download_audio.place(width=WIDTH/2-3, height=24, x=WIDTH/2+1, y=2)

# run loop
window.mainloop()