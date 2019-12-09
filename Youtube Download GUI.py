import tkinter as tk
import os, youtube_dl, concurrent.futures, requests, urllib.request
import time
import html
from PIL import Image, ImageTk
from io import BytesIO

#program vars/setup
WIDTH = 1280
HEIGHT = 800     
VIDEOLINKS = []
WINDOW = tk.Tk()
WINDOW.resizable(0,0)
WINDOW.title( "Youtube-dl GUI")
CONSOLEOUTPUT = tk.StringVar()

#check for directories
if not os.path.exists('thumbnails'):
    os.mkdir('thumbnails')
if not os.path.exists('songs'):
    os.mkdir('songs')
if not os.path.exists('videos'):
    os.mkdir('videos')


#   InfoContainer: a container for the video information
#                  uses urllib to get the thumbnail as it's faster than using youtube-dl
#                  uses requests to get the title as it's faster than using youtube-dl
# class InfoContainer:
#     def __init__(self, url):
#         #self.data = youtube_dl.YoutubeDL.
#         self.url = url
#         self.id = self.url[self.url.index('=')+1:] #Grabs the video id
#         self.thumbpath = str("./thumbnails/" + self.id)
#         # get title (faster to scrape than using youtube-dl)
#         self.title = BeautifulSoup( requests.get(self.url).text, 'html.parser' )
#         self.title.prettify('utf-8')
#         self.title = self.title.find('span', attrs={'class': 'watch-title'})
#         self.title = self.title.text.strip()
#         # get thumbnail
#         if not os.path.isfile(str(self.thumbpath + ".jpg")):
#             self.imgURL = "http://i1.ytimg.com/vi/" + self.id + "/hqdefault.jpg"
#             urllib.request.urlretrieve(self.imgURL, str(self.thumbpath + ".jpg"))
#         self.img = Image.open(str(self.thumbpath + ".jpg"))
#         self.img = self.img.resize((192,108), Image.ANTIALIAS)
#         self.img = ImageTk.PhotoImage(self.img)    

class InfoContainer:
    def __init__(self, url):
        self.url = url
        self.id = self.url[self.url.index('=')+1:] #Grabs the video id
        self.thumbpath = str("./thumbnails/" + self.id)
        # get title (faster to scrape than using youtube-dl)
        #p1 = time.perf_counter()
        self.title = requests.get(self.url).text
        self.title = self.title[self.title.index("<title>")+7:self.title.index("</title>")-10]
        self.title = html.unescape(self.title)
        #print(f'Finished in {round(time.perf_counter()-p1, 2)} second(s)')
        # get thumbnail
        self.imgURL = "http://i1.ytimg.com/vi/" + self.id + "/hqdefault.jpg"
        if not os.path.isfile(str(self.thumbpath + ".jpg")):
            self.imgURL = "http://i1.ytimg.com/vi/" + self.id + "/hqdefault.jpg"
            urllib.request.urlretrieve(self.imgURL, str(self.thumbpath + ".jpg"))
        self.img = Image.open(str(self.thumbpath + ".jpg"))
        self.img = self.img.resize((192,108), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(self.img)       
        
#   Element:        enables the visual information to be displayed
class Element:
    def __init__(self, url, f, v):
        # create vars/widgets
        self.info = InfoContainer(url)
        self.frame = tk.Frame(f, bg='#262626')
        self.thumbnail = tk.Label(self.frame, image=self.info.img, bg='#303030')
        self.description = tk.Label(self.frame, text=self.info.title, bg='#363636', fg='#f6e080')
        self.remove = tk.Button(self.frame, text='Remove', bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0,command=lambda: RemoveFromList(self.info.url, f, v))
        # place widgets
        self.frame.place(width=WIDTH-4, height=112, x=2, y=2+(v.index(self.info.url)*112))
        self.thumbnail.place(width=192, height=108, x=0, y=2)
        self.description.place(width=WIDTH-266, height=108, x=192, y=2)
        self.remove.place(width=70, height=108, x=WIDTH-74, y=2)

#   Logger:         enables debug/warning/error loggin from youtube-dl
class Logger(object):
    def debug(self, msg):
        PrintToConsole(msg)
    
    def warning(self, msg):
        PrintToConsole(msg)
    
    def error(self, msg):
        PrintToConsole(msg)


#functions
def PrintToConsole(msg):
    t_console.configure(state=tk.NORMAL)
    t_console.insert(tk.END, msg + '\n')
    t_console.configure(state=tk.DISABLED)

def YoutubeHook(d):
    if d['status'] == 'downloading':
        PrintToConsole("[" + d['filename'] + "] " + d['_percent_str'] + "  ETA: " + d['_eta_str'])

    if d['status'] == 'finished':
        PrintToConsole('Download Complete')

def _bound_to_mousewheel(self, event):
    self.t_console.bindall("<MouseWheel>", self._on_mousewheel)

def _unbound_to_mousewheel(self, event):
    self.t_console.unbind_all("<MouseWheel>")

def _on_mousewheel(self, event):
    self.t_console.yview_scroll(int(-1*(event.delta/120)), "units")

def ThreadHandler(func, *args):
    executor = concurrent.futures.ThreadPoolExecutor()
    futures = executor.submit(func, *args)

def ClearList(f, v):
    VIDEOLINKS.clear()
    ThreadHandler(UpdateList, f, v)

def UpdateList(f,v):
    for widget in f.winfo_children():
        widget.destroy()

    for url in v:
        Element(url, f, v)

def RemoveFromList(url, f, v):
    if url != "":
        v.pop(v.index(url))
        ThreadHandler(UpdateList, f, v)

def AddToList(url, f, v):
    if url != "" and v.count(url) == 0:
        v.append(url)
        ThreadHandler(UpdateList, f, v)
        i_input.delete(0, tk.END)

def DownloadList(opts, f, v):
    if len(v) > 0:
        for widget in f_data.winfo_children():
            widget.destroy()
        for url in VIDEOLINKS:
            with youtube_dl.YoutubeDL(opts) as ydl:
                ydl.download([url])
        ClearList(f, v)
        PrintToConsole("Merging/Converting Complete")

#youtube-dl option vars
video = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'progress_hooks': [YoutubeHook],
    'ignoreerrors': True,
    #'logger': Logger(),
}

audio = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'progress_hooks': [YoutubeHook],
    'ignoreerrors': True,
    #'logger': Logger(),
    'postprocessors': [
            {
            'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
            'key': 'FFmpegMetadata'
            },
        ],
}

#create layout
#   create buffer
buffer = tk.Canvas(WINDOW, height=HEIGHT, width=WIDTH, bg='black', highlightthickness=0)
buffer.pack()

#   url processor
#       input frame
f_input = tk.Frame(buffer, bg='#262626')
f_input.place(relx=0, rely=0, relwidth=1, height=28)
#       input label
l_input = tk.Label(buffer, text='Youtube Link:', font=('Arial', 8), bg='#303030', fg='#f6e080', bd=0)
l_input.place(width=89, height=24, x=2, y=2)
#       input entry
i_input = tk.Entry(f_input, font=('Arial', 8), bg='#363636', fg='#f6e080', bd=0, relief=tk.FLAT)
i_input.place(width=WIDTH-89-4-70, height=24, x=91, y=2)
i_input.focus_set()
#       input button
b_input = tk.Button(buffer, text='Add', bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0, command=lambda: ThreadHandler(AddToList(i_input.get(), f_data, VIDEOLINKS)))
b_input.place(width=70, height=24, x=WIDTH-72, y=2)

#   data frame
f_data = tk.Frame(buffer, bg='#202020')
f_data.place(width=WIDTH, height=HEIGHT-28-26-204, x=0, y=HEIGHT-(HEIGHT-28))

#   console output
#       console frame
f_console = tk.Frame(buffer, bg='#262626')
f_console.place(width=WIDTH, height = 204, x=0, y=HEIGHT-26-204)
#       console textbox
t_console = tk.Text(f_console, width=WIDTH-4, bg='#262626', fg='#f6e080', relief=tk.FLAT, state=tk.DISABLED)
t_console.pack(side=tk.LEFT, anchor=tk.N)

#   download buttons
#       download frame
f_download = tk.Frame(buffer, bg='#262626')
f_download.place(width=WIDTH, height=26, x=0, y=HEIGHT-26)
#       download video
b_download_video = tk.Button(f_download, text="Download Video", bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0, command=lambda: ThreadHandler(DownloadList(video, f_data, VIDEOLINKS)))
b_download_video.place(width=WIDTH/2-3, height=24, x=2, y=2)
#       download audio
b_download_audio = tk.Button(f_download, text="Download Audio", bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0, command=lambda: ThreadHandler(DownloadList(audio, f_data, VIDEOLINKS)))
b_download_audio.place(width=WIDTH/2-3, height=24, x=WIDTH/2+1, y=2)

#main loop
WINDOW.mainloop()