import DictionaryBuilder as DB  # import preprocessing engine, initialize as DB object
import tkinter as tk
import pandas as pd
from tkinter import *  # Gui interface library
from tkinter.ttk import *  # combobox
from Levenshtein import distance  # Levenshtein distance library
import nltk  # natural language toolkit
from nltk.tokenize import word_tokenize

# pop up function
def onPopup(event, errorword, prefixword, detector):
    # display the popup menu
    errorword = errorword.lower()  # convert to lower
    suggested_words = []  # list of suggested words, reset on every popup function call
    if detector == 'Non Word':
        for suggested_word in DB.filteredTokens:  # loop over all unique tokens
            if errorword != suggested_word:
                min_edit_distance = distance(errorword, suggested_word)  # measure minimum edit distance
                frequency = DB.uniq_token_freq[suggested_word]
                suggested_words.append(
                    # Non word error does not have measurement of maximum likelihood implemented, default as none
                    (suggested_word, '-' ,min_edit_distance, frequency)
                )
    elif detector == 'Real Word':
        # first word of bigram user input is valid
        bigramList = DB.bigramFreqTable[DB.bigramFreqTable.loc[:,'prefix'] == prefixword]
        for index, row in bigramList.iterrows():
            min_edit_distance = distance(errorword, row[1])  # measure minimum edit distance
            if errorword != row[0]:  # dont include self
                suggested_words.append(
                    # Best Matched Word, Maximum Likelihood, MED, Frequency
                    (row[1], row[3], min_edit_distance, row[2])
                )

    # convert suggestion list into a dataframe with following columns:
    suggested_words = pd.DataFrame(suggested_words, columns = ['Best Matched Word', 'Maximum Likelihood', 'MED', 'Frequency'])
    # sort dataframe according to columns hierarchy level
    suggested_words = suggested_words.sort_values(['Maximum Likelihood', 'MED', 'Frequency', 'Best Matched Word'],
                                                  ascending=[False, True, False, True])

    popup = Menu(root, tearoff=0)
    popup.add_command(label=('{0} | {1} | {2} | {3}'.format('Best Matched Word', 'Maximum Likelihood', 'MED', 'Frequency')))
    popup.add_separator()

    i = 0
    for label in suggested_words.iterrows():
        popup.add_command(label=('{0} | {1} | {2} | {3}'.format(label[1]['Best Matched Word'], label[1]['Maximum Likelihood'],
                                                                label[1]['MED'], label[1]['Frequency'])))
        i += 1
        if i > 10:
            break

    popup.tk_popup(event.x_root + 180, event.y_root, 0)
    popup.grab_release()

class Init(object):
    def __init__(self):
        root.title('Spellcheck System')
        root.geometry('700x300')
        MainFrame()
        SearchFrame()

class MainFrame(object):
    def __init__(self):
        self.combo = Combobox(root, state='readonly', values = ['Non Word', 'Real Word'])
        self.combo.current(0)
        self.combo.grid(row = 0, column = 0)
        self.btn = Button(root, text='Scan', command=self.ScanResult)
        self.btn.grid(row = 0, column = 1)
        self.Textarea()
        self.wordcountlbl = Label(root, text='Word Count: 0')
        self.wordcountlbl.grid(row = 2, column = 0)

    def Textarea(self):
        self.txtareaframe = Frame(root)
        self.txtareaframe.grid(row=1, column=0, columnspan = 2)
        self.scroll = Scrollbar(self.txtareaframe)
        self.scroll.pack(side=RIGHT, fill = Y)
        self.txtarea = Text(self.txtareaframe, wrap=WORD, yscrollcommand = self.scroll.set, height=10, width=50)
        self.txtarea.pack()
        self.txtarea.bind('<KeyPress>', self.onKeyPress)  # bind on keydown event
        self.txtarea.bind('<KeyRelease>', self.onKeyRelease)  # bind on keyrelease event
        self.scroll.config(command=self.txtarea.yview)

    def onKeyPress(self, event):
        global oriVal  # declare as global variable accessible by all members in the same class
        oriVal = self.txtarea.get('1.0', END)  # get current textarea value from beginning to end index

    def onKeyRelease(self, event):
        iCount = 0
        trimValue = ''

        for str in self.txtarea.get('1.0', END).split():  # get all user input strings
            if (iCount == 500):  # maximum 500 words only

                break

            if (trimValue != ''):
                trimValue += ' '

            trimValue += str
            iCount += 1

        if iCount < 500:
            trimValue = oriVal  # no trimming is required

        if (trimValue != oriVal):  # if user copy and paste the whole paragraphs
            self.txtarea.delete('1.0', END)  # remove all values in the textarea
            self.txtarea.insert(INSERT, trimValue)  # insert clipboard value

        self.WordCounter(iCount)

    def WordCounter(self, iCount):
        # update words count
        self.wordcountlbl.configure(text='Word Count: {0}'.format(iCount))

    def ScanResult(self):
        arbitary_word = ''
        prefix = ''
        suffix = ''

        detector = self.combo.get()  # Non Word or Real Word option selected

        global error_word_dict

        # reset highlight
        if error_word_dict:
            for error_word in error_word_dict:
                self.txtarea.tag_remove(error_word, '1.0', END)
        # end reset

        input = self.txtarea.get('1.0', END)

        if detector == 'Non Word':
            for word in input.split():
                if word:
                    if word.lower() not in DB.filteredTokens:
                        prefixidx = 0
                        suffixidx = len(word)
                        # first error word highlight start point coordinate
                        pos_start = self.txtarea.search(word, '1.0', END)
                        pos_end = 0

                        while prefixidx < len(input):
                            # if index starts from 0, default to 0
                            earlier_prefix_idx = prefixidx - 1
                            if earlier_prefix_idx < 0:
                                earlier_prefix_idx = 0

                            prefix = input[earlier_prefix_idx:prefixidx]  # character before initial prefix value
                            suffix = input[suffixidx:suffixidx + 1]  # character after suffix value
                            errorword = input[prefixidx:suffixidx]  # current slided word

                            offset = '+%dc' % len(word)  # add off set coordinate

                            if (errorword.lower() == word.lower()):
                                pos_end = pos_start + offset  # highlight end point coordinate

                            # add tag
                            if (errorword.lower() == word.lower() and (not re.findall('^[A-Za-z0-9]', prefix))
                            and (not re.findall('^[A-Za-z0-9]', suffix))):

                                if word not in error_word_dict:
                                    error_word_dict.append(word.lower())

                                self.txtarea.tag_configure(errorword, background='blue', foreground='white')  # non word error
                                self.txtarea.tag_add(errorword, pos_start, pos_end)
                                # right click event
                                self.txtarea.tag_bind(errorword, '<Button-3>', lambda event, arg1 = errorword, arg2 = '',
                                                                                      arg3 = detector : onPopup(event, arg1, arg2, arg3))


                            # search again from pos_end to the end of text (END)
                            if (errorword.lower() == word.lower()):
                                pos_start = self.txtarea.search(word, pos_end, END)

                            prefixidx += 1  # slide forward by 1 character
                            suffixidx += 1  # slide forward by 1 character
        elif detector == 'Real Word':
            input_tokenized = word_tokenize(input.lower())  # tokenize input sentence
            input_bigrams = []  # reset the list on scanning
            input_bigrams = list(nltk.bigrams(word_tokenize(input)))
            pos_start = ''

            for bigram in input_bigrams:  # begin looping the input bigram
                valid1, valid2 = False, False
                for dictWord in DB.filteredTokens:  # search through dictionary
                    input_prefix, input_suffix = bigram[0], bigram[1]

                    if (input_prefix.lower() == dictWord and valid1 == False):
                        valid1 = True

                    if (input_suffix.lower() == dictWord and valid2 == False):
                        valid2 = True

                    # both words are valid in corpus bigram, stop looping to save resources
                    if (valid1 == True and valid2 == True):
                        break

                if (valid1 == True and valid2 == True): # both words in bigram are valid and exist in dictionary
                    errorword = input_suffix
                    sentence = '{0} {1}'.format(input_prefix, input_suffix)

                    if sentence not in error_word_dict:  # if real word error not exists in the list
                        error_word_dict.append(sentence.lower())

                    # first error word highlight start point coordinate
                    pos_sent_start = self.txtarea.search(sentence, '1.0', END)
                    # add off set coordinate
                    sent_offset = '+%dc' % len(pos_sent_start)

                    if not pos_start:  # initialize with first suffix word detected
                        pos_start = self.txtarea.search(errorword, '1.0', END)
                    else:  # refresh starting point of highlight based on last bigram stop point
                        pos_start = self.txtarea.search(errorword, pos_sent_start, END)

                    offset = '+%dc ' % len(errorword)

                    while pos_sent_start:
                        pos_sent_end = pos_sent_start + sent_offset
                        pos_end = pos_start + offset
                        nrow = len(DB.bigramFreqTable[(DB.bigramFreqTable['prefix'] == input_prefix.lower()) &
                                                      (DB.bigramFreqTable['suffix'] == input_suffix.lower())].index)

                        if nrow == 0:  # if the input bigram pair dont exist in corpus bigram pair, highlight
                            # please do not insert Enter in the textarea otherwise the highlight feature will break
                            # due to positioning measurement limitation
                            self.txtarea.tag_configure(sentence, background='blue',
                                                       foreground='white')  # read word error
                            self.txtarea.tag_add(sentence, pos_start, pos_end)
                            self.txtarea.tag_bind(sentence, '<Button-3>',
                                                  lambda event, arg1=input_suffix.lower(), arg2= input_prefix.lower(),
                                                         arg3=detector: onPopup(event, arg1, arg2, arg3))  # right click event

                        # search again from pos_end to the end of text (END)
                        pos_sent_start = self.txtarea.search(sentence, pos_sent_end, END)
                        pos_start = pos_sent_end


class SearchFrame(object):
    def __init__(self):
        self.searchlbl = Label(root, text = 'Search: ')
        self.searchlbl.grid(row = 0, column = 2)
        self.searchinput = Entry(root, width = 25)
        self.searchinput.grid(row = 0, column = 3)
        self.searchinput.bind('<BackSpace>', self.Search) #bind on backspace event
        self.searchinput.bind('<KeyRelease>', self.Search) #bind on keyrelease event
        self.filteredTokens = DB.filteredTokens
        self.Dictionary()

    def Search(self, event):
        searchInput = self.searchinput.get()

        new_dict = [i for i in DB.filteredTokens if searchInput in i.lower()]

        if new_dict:
            self.filteredTokens = new_dict
        else:
            self.filteredTokens = []

        if not searchInput:
            self.filteredTokens = DB.filteredTokens

        self.DictionaryList()

    def Dictionary(self):
        self.resultlbl = Label(root, text = 'Dictionary')
        self.resultlbl.grid(row = 1, column = 2)
        self.dictframe = Frame(root)
        self.dictframe.grid(row = 1, column = 3)
        self.dictscrollbar = Scrollbar(self.dictframe)
        self.dictscrollbar.pack(side=RIGHT, fill=Y)
        self.dictlistbox = Listbox(self.dictframe, yscrollcommand = self.dictscrollbar.set)
        self.DictionaryList()
        self.dictlistbox.pack(side = LEFT, fill = BOTH)
        self.dictscrollbar.config(command = self.dictlistbox.yview)

    def DictionaryList(self):
        self.dictlistbox.delete(0, END) #initially remove all items
        for word in sorted(self.filteredTokens):
            self.dictlistbox.insert(END, str(word))


root = tk.Tk()
error_word_dict = []

Init()

