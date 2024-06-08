import os
import random
import json
import tkinter
from tkinter import *
from tkinter import filedialog
from io import BytesIO
from ctypes import *
from ctypes.wintypes import *
from PIL import ImageDraw, ImageFont
from PIL import Image as IMGI

defaultSet = '''{
    "NameColor": {
        "Default": [0, 0, 0]
    },
    "NameStroke": {
        "Default": [255, 255, 255]
    },
    "NameFont": {
        "Default": "Arial"
    },
    "PrevFol": {
        "Prev": "None"
    }
}'''

if not os.path.exists("subtalker.ini"):
    with open("subtalker.ini", "w") as config_file:
        config_file.write(defaultSet)
    with open('subtalker.ini') as ini:
        settings = json.load(ini)
else:
    with open('subtalker.ini') as ini:
        settings = json.load(ini)

def convert_lists_to_tuples(d):
    for key, value in d.items():
        if isinstance(value, list):
            d[key] = tuple(value)
        elif isinstance(value, dict):
            convert_lists_to_tuples(value)

def add_font_paths(font_dict, font_folder):
    for key, font_name in font_dict.items():
        font_dict[key] = os.path.join(font_folder, font_name + '.ttf')

user_home_dir = os.path.expanduser("~")
user_font_folder = os.path.join(user_home_dir, 'AppData', 'Local', 'Microsoft', 'Windows', 'Fonts')

convert_lists_to_tuples(settings['NameColor'])
convert_lists_to_tuples(settings['NameStroke'])
convert_lists_to_tuples(settings['NameFont'])

add_font_paths(settings['NameFont'], user_font_folder)

NameColor = settings['NameColor']
NameStroke = settings['NameStroke']
NameFont = settings['NameFont']
PrevFol = settings['PrevFol']

Names = list(NameColor.keys())

n = ("")
imagepath = ''

if PrevFol["Prev"] != 'None':
    imagepath = PrevFol['Prev']

########################################

HGLOBAL = HANDLE
SIZE_T = c_size_t
GHND = 0x0042
GMEM_SHARE = 0x2000

GlobalAlloc = windll.kernel32.GlobalAlloc
GlobalAlloc.restype = HGLOBAL
GlobalAlloc.argtypes = [UINT, SIZE_T]

GlobalLock = windll.kernel32.GlobalLock
GlobalLock.restype = LPVOID
GlobalLock.argtypes = [HGLOBAL]

GlobalUnlock = windll.kernel32.GlobalUnlock
GlobalUnlock.restype = BOOL
GlobalUnlock.argtypes = [HGLOBAL]

CF_DIB = 8

OpenClipboard = windll.user32.OpenClipboard
OpenClipboard.restype = BOOL
OpenClipboard.argtypes = [HWND]

EmptyClipboard = windll.user32.EmptyClipboard
EmptyClipboard.restype = BOOL
EmptyClipboard.argtypes = None

SetClipboardData = windll.user32.SetClipboardData
SetClipboardData.restype = HANDLE
SetClipboardData.argtypes = [UINT, HANDLE]

CloseClipboard = windll.user32.CloseClipboard
CloseClipboard.restype = BOOL
CloseClipboard.argtypes = None

############################################

def choose_folder():
    global imagepath
    imagepath = filedialog.askdirectory()
    with open('subtalker.ini', 'r') as ini:
        filedata = ini.read()
    index_start = filedata.find('"Prev": "')
    if index_start != -1:
        index_end = filedata.find('"', index_start + len('"Prev": "'))
        if index_end != -1:
            new_filedata = filedata[:index_start + len('"Prev": "')] + imagepath + filedata[index_end:]
            with open('subtalker.ini', 'w') as file:
                file.write(new_filedata)

def is_image_file(filename):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

FileList = []

def Talk():

    if imagepath == '':
        footer_text.set("Choose a folder")
        return

    for root, dirs, files in os.walk(imagepath):
        for file in files:
            if is_image_file(file):
                FileList.append(os.path.join(root, file))

    Framlen = sum(len(files) for _, _, files in os.walk(imagepath))

    while True:
        n = Name.get()
        Color = NameColor[n]
        Stroke = NameStroke[n]
        FontN = NameFont[n]
        FrameNum = random.randint(1,Framlen-1)
        GetFrame = FileList[FrameNum]
        footer_text.set(GetFrame)
        print(GetFrame)
        Image = IMGI.open(GetFrame)
        draw = ImageDraw.Draw(Image)
        _L, _T, maxR, maxB = Image.getbbox()
        RWid = random.randint(1, maxR)
        RHig = random.randint(1, maxB)
        INPUT = entry.get()
        LINES = INPUT.replace('\\n', '\n')
        NUMLIN = LINES.count('\n') + 1
        font = ImageFont.truetype(FontN, 80)
        FindLong = max(LINES.splitlines(),key=len,default=1)
        _l, _t, TX, XT = font.getbbox(str(FindLong))
        if RWid + TX > maxR:
            RWid = abs(RWid - TX)
        if RHig + XT > maxB:
            RHig = abs(RHig - XT)
        Left = RWid - 15
        Upper = RHig
        Right = Left + TX + 30
        if NUMLIN == 1:
            Lower = Upper + XT + 25
        else:
            Lower = Upper + XT * 1.2 * NUMLIN

        if (Lower - Upper) < (maxB - Upper - Lower - Upper) and RWid < ((maxR-_L) - (RWid - maxR)):
            break

        footer_text.set('Looking for an image that fits')
        window.update()

    draw.text((RWid, RHig), str(LINES), fill=(Color), font=font, stroke_fill=(Stroke), stroke_width=6, align='center')

    box = (Left, Upper, Right, Lower)
    Cropped = Image.crop(box)
    window.update()

    output = BytesIO()
    Cropped.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    hData = GlobalAlloc(GHND | GMEM_SHARE, len(data))
    pData = GlobalLock(hData)
    memmove(pData, data, len(data))
    GlobalUnlock(hData)

    OpenClipboard(None)
    EmptyClipboard()
    SetClipboardData(CF_DIB, pData)
    CloseClipboard()
    pass


window = Tk()
window.title("SubTalker")
icon = PhotoImage(file='\HitaCube.png')

window.config(background='#4A4A4A')
window.iconphoto(True, icon)

folder_button = Button(window, text='Choose Folder', command=choose_folder, font=('Magra', 16, 'bold'), fg="white", background='gray', activebackground='gray', activeforeground='gray', width=24)
folder_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

Name = StringVar(window)
Name.set(Names[0])

footer_text = tkinter.StringVar()
footer_label = tkinter.Label(window, textvariable=footer_text, bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W, width=50)
footer_label.grid(row=3, column=0, columnspan=2, sticky="we", padx=5, pady=5)

drop = OptionMenu(window, Name, *Names)
drop.config(font=('Magra', 16, 'bold'))
drop.config(fg="white")
drop.config(background='gray')
drop.config(activeforeground='gray')
drop.config(width=30)
drop.grid(row=0, column=1, padx=5, pady=5, sticky="we")

entry = Entry(window, font=('Magra', 20, 'bold'))
entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="we")

button = Button(window, text='Copy to Clipboard', command=Talk, font=('Magra', 20, 'bold'), fg="white", background='gray', activebackground='gray', activeforeground='gray', width=23)
button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="we")

window.bind('<Return>', lambda event=None: button.invoke())

window.mainloop()
