import tkinter as tk
import os, youtube_dl, concurrent.futures, requests, urllib.request, time, html
from PIL import Image, ImageTk


#program vars/setup
WIDTH = 1280
HEIGHT = 800     
VIDEOLINKS = []
WINDOW = tk.Tk()
WINDOW.resizable(0,0)
WINDOW.title( "Youtube-dl GUI")
CONSOLEOUTPUT = tk.StringVar()
WIDGETDATA = {}
SCROLLDATA = {
    'height': 0,
    'amount': 0,
    }

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
class InfoContainer:
    def __init__(self, url):
        self.url = url
        self.id = self.url[self.url.index('=')+1:]
        self.thumbpath = ''.join(["./thumbnails/", self.id])
        self.title = requests.get(''.join(["https://www.youtube.com/embed/",self.id])).text
        self.title = self.title[self.title.index("<title>")+7:self.title.index("</title>")-10]
        self.title = html.unescape(self.title)
        self.imgURL = ''.join(["ttp://i1.ytimg.com/vi/", self.id, "/sddefault.jpg"])
        if not os.path.isfile(''.join([self.thumbpath, ".jpg"])):
            self.imgURL = ''.join(["http://i1.ytimg.com/vi/", self.id, "/hqdefault.jpg"])
            urllib.request.urlretrieve(self.imgURL, ''.join([self.thumbpath, ".jpg"]))
        self.img = Image.open(''.join([self.thumbpath, ".jpg"]))
        self.img = self.img.resize((192,108), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(self.img)


#   Element:        enables the visual information to be displayed
class Element:
    def __init__(self, url, f, v, i, sd):
        self.info = i
        self.frame = tk.Frame(f, bg='#262626')
        self.thumbnail = tk.Label(self.frame, image=self.info.img, bg='#303030')
        self.description = tk.Label(self.frame, text=self.info.title, bg='#363636', fg='#f6e080')
        self.remove = tk.Button(self.frame, text='Remove', bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', highlightcolor='#262626', relief=tk.FLAT, bd=0,command=lambda: RemoveFromList(self.info.url, f, v))
        self.frame.place(width=WIDTH-4, height=112, x=2, y=2+(v.index(self.info.url)*112)+sd['amount'])
        self.thumbnail.place(width=192, height=108, x=0, y=2)
        self.description.place(width=WIDTH-266, height=108, x=192, y=2)
        self.remove.place(width=70, height=108, x=WIDTH-74, y=2)


#   Perf:           performance logger for functions
class Performance:
    def __init__(self):
        self.start = 0
    
    def Start(self):
        self.start = time.perf_counter()

    def Stop(self):
        if self.start == 0:
            print('Start function not called \n')
        else:
            print(f'Finished in {round(time.perf_counter()-self.start, 2)} second(s)')
perf = Performance()


#functions
def PrintToConsole(msg):
    t_console.configure(state=tk.NORMAL)
    t_console.insert(tk.END, ''.join([msg, '\n']))
    t_console.configure(state=tk.DISABLED)
    t_console.yview(tk.END)

def YoutubeHook(d):
    if d['status'] == 'downloading':
        PrintToConsole(''.join(["[", d['filename'], "] ", d['_percent_str'], " : ", str(d['downloaded_bytes']), "/", str(d['total_bytes'])]))

    if d['status'] == 'finished':
        PrintToConsole(''.join(['Download Complete: ', d['filename']]))

def _onMousewheel(event):
    if event.widget is t_console:
        print("Yes")
        event.widget.yview_scroll(int(-1*(event.delta/120)), "units")
    else:
        SCROLLDATA['amount'] += (-1 * event.delta)
        if SCROLLDATA['amount'] < 0:
            SCROLLDATA['amount'] = 0
        UpdateList(f_data, VIDEOLINKS)

def _select_all(event):
    i_input.select_range(0, tk.END)
    i_input.icursor(tk.END)
    return 'break'

def _submit(event):
    AddToList(i_input.get(), f_data, VIDEOLINKS)

def ThreadHandler(func, *args):
    executor = concurrent.futures.ThreadPoolExecutor()
    futures = executor.submit(func, *args)

def ClearList(f, v):
    VIDEOLINKS.clear()
    WIDGETDATA.clear()
    UpdateList(f, v)

def UpdateList(f,v):
    for widget in f.winfo_children():
        widget.destroy()

    for url in v:
        Element(url, f, v, WIDGETDATA[url], SCROLLDATA)

def RemoveFromList(url, f, v):
    if url != "":
        v.pop(v.index(url))
        WIDGETDATA.pop(url)
        UpdateList(f, v)

def AddToList(url, f, v):
    if url != "" and not url in v:
        v.append(url)
        ThreadHandler(AddData, url, f, v)
        i_input.delete(0, tk.END)

def AddData(url, f, v):
    WIDGETDATA.update({url: InfoContainer(url)})
    UpdateList(f, v)

def DownloadList(opts, f, v):
    if len(v) > 0:
        PrintToConsole("Download Starting...")
        for widget in f_data.winfo_children():
            widget.destroy()
        for url in VIDEOLINKS:
            with youtube_dl.YoutubeDL(opts) as ydl:
                ydl.download([url])
        ClearList(f, v)
        PrintToConsole("Merging/Converting Complete")
    else:
        PrintToConsole("Nothing to download")

#youtube-dl option vars
video = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': '/videos/%(title)s.%(ext)s',
    'progress_hooks': [YoutubeHook],
    'ignoreerrors': True,
}

audio = {
    'format': 'bestaudio/best',
    'outtmpl': '/songs/%(title)s.%(ext)s',
    'progress_hooks': [YoutubeHook],
    'ignoreerrors': True,
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
#   create buffer (base widget)
buffer = tk.Canvas(WINDOW, height=HEIGHT, width=WIDTH, bg='black', highlightthickness=0)
buffer.pack()

#   url processor bar
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
i_input.bind('<Control-a>', _select_all)
i_input.bind('<Return>', _submit)
#       input add button
b_input = tk.Button(buffer, text='Add', bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0, command=lambda: AddToList(i_input.get(), f_data, VIDEOLINKS))
b_input.place(width=70, height=24, x=WIDTH-72, y=2)

#   data frame container (Contains all the visual information widgets after adding a YouTube video)
f_data = tk.Frame(buffer, bg='#202020')
f_data.place(width=WIDTH, height=HEIGHT-28-26-204, x=0, y=28)
WINDOW.bind('<MouseWheel>', _onMousewheel)
#   console output
#       console frame
f_console = tk.Frame(buffer, bg='#262626')
f_console.place(width=WIDTH, height = 204, x=0, y=HEIGHT-230)
#       console textbox
t_console = tk.Text(f_console, width=WIDTH-4, bg='#262626', fg='#f6e080', relief=tk.FLAT, state=tk.DISABLED)
t_console.pack(side=tk.LEFT, anchor=tk.N)

#   download buttons
#       download frame
f_download = tk.Frame(buffer, bg='#262626')
f_download.place(width=WIDTH, height=26, x=0, y=HEIGHT-26)
#       download video button
b_download_video = tk.Button(f_download, text="Download Video", bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0, command=lambda: ThreadHandler(DownloadList, video, f_data, VIDEOLINKS))
b_download_video.place(width=WIDTH/2-3, height=24, x=2, y=2)
#       download audio button
b_download_audio = tk.Button(f_download, text="Download Audio", bg='#303030', fg='#f6e080', activebackground='#262626', activeforeground='#f6e080', relief=tk.FLAT, bd=0, command=lambda: ThreadHandler(DownloadList, audio, f_data, VIDEOLINKS))
b_download_audio.place(width=WIDTH/2-3, height=24, x=WIDTH/2+1, y=2)

#main loop
WINDOW.mainloop()