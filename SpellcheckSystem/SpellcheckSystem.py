import DictionaryBuilder as DB
import tkinter as tk
import pandas as pd
from tkinter import *  # Gui interface library
from tkinter.ttk import * #combobox
from Levenshtein import distance  #Levenshtein distance library
import nltk #natural language toolkit
from nltk.tokenize import word_tokenize

def onPopup(event, errorword, prefixword, detector):
    # display the popup menu
    errorword = errorword.lower() #convert to lower
    suggested_words = [] #list of suggested words
    if detector == 'Non Word':
        for suggested_word in DB.filteredTokens:
            if errorword != suggested_word:
                min_edit_distance = distance(errorword, suggested_word)
                frequency = DB.uniq_token_freq[suggested_word]
                suggested_words.append(
                    # Non word error does not have measurement of maximum likelihood implemented, default as 0
                    (suggested_word, min_edit_distance, frequency, 0)
                )
    elif detector == 'Real Word':
        bigramList = DB.bigramFreqTable[DB.bigramFreqTable.loc[:,'prefix'] == prefixword]
        for index, row in bigramList.iterrows():
            med = distance(errorword, row[1])
            if errorword != row[1]: #dont include self
                suggested_words.append(
                    # MSuggested Word, MED, Frequency, Ratio,
                    (row[1], med, row[2], row[3])
                )

    suggested_words = pd.DataFrame(suggested_words, columns = ['Suggested Word', 'Minimum Edit Distance', 'Frequency', 'Ratio'])
    suggested_words = suggested_words.sort_values(['Minimum Edit Distance', 'Frequency', 'Ratio', 'Suggested Word'], ascending=[True, False, False, True])

    popup = Menu(root, tearoff=0)
    popup.add_command(label=('{0} | {1} | {2}'.format('Best Matched Word', 'MED', 'Frequency')))
    popup.add_separator()

    i = 0
    for label in suggested_words.iterrows():
        popup.add_command(label=('{0} | {1} | {2}'.format(label[1]['Suggested Word'], label[1]['Minimum Edit Distance'], label[1]['Frequency'])))
        i += 1
        if i > 10:
            break

    popup.tk_popup(event.x_root, event.y_root, 0)
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
        global oriVal
        oriVal = self.txtarea.get('1.0', END)

    def onKeyRelease(self, event):
        if (len(self.txtarea.get('1.0', END)) > 500):
            trimValue = self.txtarea.get('1.0', END)[:499]
        else:
            trimValue = oriVal

        if (trimValue != oriVal):
            self.txtarea.delete('1.0', END)
            self.txtarea.insert(INSERT, trimValue)

    def ScanResult(self):
        arbitary_word = ''
        prefix = ''
        suffix = ''

        detector = self.combo.get() #Non Word or Real Word

        global error_word_dict

        # reset highlight
        if error_word_dict:
            for error_word in error_word_dict:
                self.txtarea.tag_remove(error_word, '1.0', END)
        # end reset

        words = self.txtarea.get('1.0', END)

        r, row, column = 1, 15, 50

        if detector == 'Non Word':
            for word in words.split():
                if word:
                    if word.lower() not in DB.filteredTokens:
                        r = 1
                        while r <= row:
                            pos_start = self.txtarea.search(word, '1.0', END)
                            c = len(word)  # reset column count upon new row
                            prefixidx = 0

                            while c <= column:
                                suffixidx = c

                                raw_text = words

                                earlier_prefix_idx = prefixidx - 1
                                if earlier_prefix_idx < 0:
                                    earlier_prefix_idx = 0

                                prefix = raw_text[earlier_prefix_idx:prefixidx]
                                suffix = raw_text[suffixidx:suffixidx + 1]
                                errorword = raw_text[prefixidx:suffixidx]

                                offset = '+%dc' % len(word)

                                if pos_start:
                                    pos_end = pos_start + offset

                                # add tag
                                if (errorword == word and (not re.findall('^[A-Za-z0-9]', prefix))
                                and (not re.findall('^[A-Za-z0-9]', suffix))):

                                    if word not in error_word_dict:
                                        error_word_dict.append(word)

                                    self.txtarea.tag_configure(errorword, background='blue', foreground='white')  # non word error
                                    self.txtarea.tag_add(errorword, pos_start, pos_end)
                                    self.txtarea.tag_bind(errorword, '<Button-3>', lambda event, arg1 = errorword, arg2 = '', arg3 = detector : onPopup(event, arg1, arg2, arg3))  # right click event

                                # search again from pos_end to the end of text (END)
                                if (errorword == word):
                                    pos_start = self.txtarea.search(word, pos_end, END)

                                c += 1 #slide forward
                                prefixidx = c - len(word)
                            r += 1
        elif detector == 'Real Word':
            input_tokenized = word_tokenize(words.lower()) #tokenize input sentence
            input_bigrams = [] #reset the list on scanning
            input_bigrams = list(nltk.bigrams(input_tokenized))
            pos_start = ''

            for bigram in input_bigrams: #begin looping the input bigram
                valid1, valid2 = False, False
                for dictWord in DB.filteredTokens: #search through dictionary
                    input_prefix, input_suffix = bigram[0], bigram[1]

                    if (input_prefix == dictWord and valid1 == False):
                        valid1 = True

                    if (input_suffix == dictWord and valid2 == False):
                        valid2 = True

                    if (valid1 == True and valid2 == True):
                        break

                if (valid1 == True and valid2 == True): #both words in bigram are valid and exist in dictionary
                    errorword = input_suffix
                    sentence = '{0} {1}'.format(input_prefix, input_suffix)

                    if sentence not in error_word_dict:
                        error_word_dict.append(sentence)

                    pos_sent_start = self.txtarea.search(sentence, '1.0', END)
                    sent_offset = '+%dc' % len(pos_sent_start)

                    if not pos_start: #initialize with first suffix word detected
                        pos_start = self.txtarea.search(errorword, '1.0', END)
                    else: #refresh starting point of highlight based on last bigram stop point
                        pos_start = self.txtarea.search(errorword, pos_sent_start, END)

                    offset = '+%dc ' % len(errorword)

                    while pos_sent_start:
                        pos_sent_end = pos_sent_start + sent_offset
                        pos_end = pos_start + offset
                        nrow = len(DB.bigramFreqTable[(DB.bigramFreqTable['prefix'] == input_prefix) &
                                                      (DB.bigramFreqTable['suffix'] == input_suffix)].index)

                        if nrow == 0: # if the input bigram pair dont exist in corpus bigram pair, highlight
                            # please do not insert Enter in the textarea otherwise the highlight feature will break due to positioning measurement limitation
                            self.txtarea.tag_configure(sentence, background='blue',
                                                       foreground='white')  # non word error
                            self.txtarea.tag_add(sentence, pos_start, pos_end)
                            self.txtarea.tag_bind(sentence, '<Button-3>',
                                                  lambda event, arg1=input_suffix, arg2= input_prefix, arg3=detector: onPopup(event, arg1, arg2, arg3))  # right click event

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
root.mainloop()


# extract prefix as estimator
# def bigram_features(prefix):
#     return {'prefix': prefix.lower()}

# Naive Bayes classifier to predict bigram suffix
# import random
# bigram_list = ([(row[0], row[1]) for index, row in DB.bigramFreqTable.iterrows()])
# random.shuffle(bigram_list)
#
# featuresets = [(bigram_features(n), bigram) for (n, bigram) in bigram_list]
# train_set, test_set = featuresets[6300:], featuresets[:6300]
# classifier = nltk.NaiveBayesClassifier.train(train_set)
#
# print(classifier.classify(bigram_features('acknowledge')))
# print(nltk.classify.accuracy(classifier, test_set))
#
# train_prefix = bigrams[6300:]
# devtest_prefix = bigrams[6300:8000]
# test_prefix = bigrams[:6300]
#
# train_set = [(bigram_features(n), suffix) for (n, suffix) in train_prefix]
# devtest_set = [(bigram_features(n), suffix) for (n, suffix) in devtest_prefix]
# test_set = [(bigram_features(n), suffix) for (n, suffix) in test_prefix]
# classifier = nltk.NaiveBayesClassifier.train(train_set)
# print(nltk.classify.accuracy(classifier, devtest_set))
#
# errors = []
# correct = []
# prediction_list = []
# for (prefix, actual) in devtest_prefix:
#     guess = classifier.classify(bigram_features(prefix))
#     prediction_list.append((actual, guess, prefix))
#     if guess != actual:
#         errors.append((actual, guess, prefix))
#     else:
#         correct.append((actual, guess, prefix))
#
# for (actual, guess, name) in sorted(errors):
#     print('actual={:<8} guess={:<8s} name={:<30}'.format(actual, guess, name))
#
# for (actual, guess, name) in sorted(correct):
#     print('actual={:<8} guess={:<8s} name={:<30}'.format(actual, guess, name))
#
# def column(matrix, i):
#     return [row[i] for row in matrix]
#
# cm = nltk.ConfusionMatrix(column(prediction_list,0), column(prediction_list,1))
# print(cm.pretty_format(sort_by_count=True))
#
# cm