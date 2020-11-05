#coding=utf8
import sys
import xlwt
import xlrd
import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.NoteStore as NoteStore
import jieba
# from Oauth import Oauth
# from Storage import Storage
from evernote.api.client import EvernoteClient

# * If you are international user, replace all the yinxiang with evernote

# SANDBOX = True
# SERVICE_HOST = 'sandbox.evernote.com'
SANDBOX = False
SERVICE_HOST = 'app.yinxiang.com'

# * If you are international user, replace all the yinxiang with evernote

# You can get this from 'https://%s/api/DeveloperToken.action'%SERVICE_HOST >>
SPECIAL_DEV_TOKEN = True
DEV_TOKEN = 'your token'
# SPECIAL_DEV_TOKEN = False
# DEV_TOKEN = ''
# In China it's https://app.yinxiang.com/api/DeveloperToken.action <<

LOCAL_STORAGE = False

class EvernoteController:


    def __init__(self):
        if DEV_TOKEN:
            self.token = DEV_TOKEN
        else:
            self.token = Oauth(SANDBOX).oauth()

        sys.stdout.write('Logging\r')
        if SANDBOX:
            self.client = EvernoteClient(token=self.token)
        else:
            self.client = EvernoteClient(token=self.token, service_host=SERVICE_HOST)
        self.userStore = self.client.get_user_store()
        self.noteStore = self.client.get_note_store()
        if LOCAL_STORAGE: self.__set_storage()
        print ('Login Succeed as {name}'.format(name=self.userStore.getUser().username))


    def __set_storage(self):
        print ('Loading Storage')
        self.storage = Storage(self.noteStore, self.token)
        print ('Storage loaded')


    def create_notebook(self,title):
        notebook = Types.Notebook()
        notebook.name = title
        notebook = self.noteStore.createNotebook(notebook)
        if LOCAL_STORAGE: self.storage.create_notebook(notebook)
        print_line('Created notebook: %s successfully'%title)


    def create_note(self, title, content, notebook = None):
        note = Types.Note()
        note.title = title
        note.content = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        note.content += content
        #'<en-note>Hello, world!</en-note>'
        if notebook: note.notebookGuid = self.myfile(notebook).guid
        note = self.noteStore.createNote(note)
        if LOCAL_STORAGE: self.storage.create_note(note, notebook)


        print_line('Created note: %s successfully' %title)


    def move_note(self, note, _to):
        if type(self.myfile(note)) != type(Types.Note()) or type(self.myfile(_to)) != type(Types.Notebook()): raise Exception('Type Error')
        self.noteStore.copyNote(self.token, self.myfile(note).guid, self.myfile(_to).guid)
        if SPECIAL_DEV_TOKEN:
            self.noteStore.expungeNote(self.token, self.myfile(note).guid)
        else:
            self.noteStore.deleteNote(self.token, self.myfile(note).guid)
        if LOCAL_STORAGE: self.storage.move_note(note, _to)
        print_line('Move %s to %s successfully'%(note,_to))


    # def delete_note(self, note):
    #     if type(self.myfile(note)) != type(Types.Note()): raise Exception('Types Error')
    #     self.noteStore.deleteNote(self.token, self.myfile(note).guid)
    #     # BUG
    #     if LOCAL_STORAGE: self.storage.delete_note(note)
    #     print_line('Deleted %s successfully'%note)
    # def delete_notebook(self, notebook):
    #     if SPECIAL_DEV_TOKEN:
    #         if type(self.myfile(notebook)) != type(Types.Notebook()): raise Exception('Types Error')
    #         self.noteStore.expungeNotebook(self.token, self.myfile(notebook).guid)
    #         # BUG
    #         if LOCAL_STORAGE: self.storage.delete_notebook(notebook)
    #         print_line('Deleted %s successfully'%notebook)

    def myfile(self, s):
        if LOCAL_STORAGE: return self.storage.myfile(s)
        f = s.split('/')
        if '/' in s:
            for nb in self.noteStore.listNotebooks():
                if nb.name == f[0]:
                    fi = NoteStore.NoteFilter()
                    fi.notebookGuid = nb.guid
                    for ns in self.noteStore.findNotes(self.token, fi, 0, 999).notes:
                        if ns.title == f[1]: return ns
        else:
            for nb in self.noteStore.listNotebooks():
                if nb.name == f[0]: return nb
        raise Exception('%s not found'%s)

    def show_notebook(self):
        if LOCAL_STORAGE:
            self.storage.show_notebook()
        else:
            for nb in self.noteStore.listNotebooks(): print_line(nb.name)

    def show_notes(self, notebook=None):
        if LOCAL_STORAGE:
            self.storage.show_notes(notebook)
        else:
            for nb in self.noteStore.listNotebooks():
                if not notebook: print_line(nb.name + ':')
                if not notebook or nb.name == notebook:
                    f = NoteStore.NoteFilter()
                    f.notebookGuid = nb.guid
                    for ns in self.noteStore.findNotes(self.token, f, 0, 999).notes:
                        print_line(('' if notebook else '') + ns.title)

    def load_notes(self, notebook=None):
        if LOCAL_STORAGE:
            self.storage.show_notes(notebook)
        else:
            for nb in self.noteStore.listNotebooks():
                if not notebook: print_line(nb.name + ':')
                if not notebook or nb.name == notebook:
                    f = NoteStore.NoteFilter()
                    f.notebookGuid = nb.guid
                    m = NoteStore.NotesMetadataResultSpec(includeTitle=True)
                    offset = 0
                    inx = 0
                    while(offset < 15829):
                      for ns in self.noteStore.findNotesMetadata(self.token, f, offset, 999,m).notes:
                        print_line(('' if notebook else '') + ns.title,inx)
                        inx += 1
                      offset = offset + 500

def print_line(s,n):
    t = sys.getfilesystemencoding()
    print (s.encode(t).decode('UTF-8'))
    worksheet.write(n, 0, s.encode(t).decode('UTF-8'))

def comeintoexcel(s,n):
    worksheet.write(n,0,s)

def read_excel(ex):
    words = []
    for i in range(ex.nrows):
      words = words + jieba.lcut(str(ex.cell(i,1).value))
    return words

def static_words(words):
    # load stopwords
    stopwords = [line.strip() for line in open("santi.txt", encoding="utf-8").readlines()]
    counts = {}
    for word in words:
        # Dont in stopwords
        if word not in stopwords:
            # Dont add one
            if len(word) == 1:
                continue
            else:
                counts[word] = counts.get(word, 0) + 1
    items = list(counts.items())
    items.sort(key=lambda x: x[1], reverse=True)
    for i in range(30):
        word, count = items[i]
        print("{:<10}{:>7}".format(word, count))

if __name__ == '__main__':
    e = EvernoteController()
    workbook = xlwt.Workbook(encoding = 'utf-8')
    worksheet = workbook.add_sheet('weibo')
    e.load_notes(notebook="微博")
    workbook.save('excel.xls')
    worksheet = xlrd.open_workbook(r'excel.xls').sheet_by_index(0)
    words = read_excel(worksheet)
    static_words(words)