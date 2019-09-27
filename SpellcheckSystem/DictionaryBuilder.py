import io #to streamread file
import os #directory locator
import re #regular expression
import string #remove punctuation
import nltk #natural language toolkit
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,
                                  password=password,
                                  caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text

CorpusPath = 'F:/APU/Modules/NLP/Assignment/Corpus document'
pdfs = os.listdir(CorpusPath)
fulltext= ''
for pdf in pdfs:
    pdftext = convert_pdf_to_txt(CorpusPath + '/' + pdf)
    fulltext = fulltext + pdftext

fulltext = fulltext.replace('\n', ' ')
fulltext = re.sub('[0-9\x0c]+', '', fulltext) #remove all digits, unicode
fulltext = re.sub(r'- ', '', fulltext) #remove breaking symbols to form complete word
content = ''

for word in fulltext.split():
    bMatch = (re.match(r'.http', word) or re.match(r'http', word)) #remove url, not important i think.....
    if not bMatch:
        content += word + ' '

tokens = []
uniq_token_freq = []
bigram_freq = {}
sent_tokenized = []
filteredTokens = []
stopTokens = stopwords.words('english') + list(string.punctuation)
word_tokens = word_tokenize(content)

for w in word_tokens:
    w = w.lower() #convert word to lower case
    if w not in stopTokens:
        w = re.sub(r'[^a-zA-Z]', '', w)
        # not an empty string after trimming
        # not repeated token
        # not single character because it is not a word
        if w and w not in filteredTokens and len(w) is not 1:
            filteredTokens.append(w)

        if w and len(w) is not 1:
            tokens.append(w)

uniq_token_freq = nltk.FreqDist(tokens)

#Bigram builder
bigrams = list(nltk.bigrams(word_tokens))
length = len(tokens)
for i in range(length - 1):
    bigram = (tokens[i], tokens[i + 1])
    if bigram not in bigram_freq:
        bigram_freq[bigram] = 0
        bigram_freq[bigram] += 1
