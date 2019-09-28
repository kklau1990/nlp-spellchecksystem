import io #to streamread file
import os #directory locator
import re #regular expression
import string #remove punctuation
import collections
import pandas as pd
import nltk #natural language toolkit
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

# non word builder section
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

stopTokens = stopwords.words('english') + list(string.punctuation)
word_tokens = word_tokenize(content) #form word token from raw content
uniq_token_freq = [] #list of unique word frequency
filteredTokens = [] #list of token to hold unique word as dictionary
tokens = [] #list of repeated word
prefix_keys = collections.defaultdict(list)
bigramFreqList = []

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

uniq_token_freq = nltk.FreqDist(tokens) # Unique token frequency
# end non word builder

# Real word builder
# Build a bigram from context
bigrams = nltk.collocations.BigramAssocMeasures() #association measurement
bigramFinder = nltk.collocations.BigramCollocationFinder.from_words(tokens) #form bigram object
scored = bigramFinder.score_ngrams(bigrams.likelihood_ratio) #calculate maximum likelihood
bigram_freq = bigramFinder.ngram_fd.items() #calculate frequency per item

for bigram in bigram_freq:
    prefix, suffix, frequency = bigram[0][0], bigram[0][1], bigram[1]

    for key, score in scored:
        key_prefix, key_suffix = key[0], key[1]

        if (key_prefix == prefix and key_suffix == suffix):
            bigramFreqList.append(
                (prefix, suffix, frequency, score)
            )

bigramFreqTable = pd.DataFrame(list(bigramFreqList),
                               columns=['prefix', 'suffix', 'freq', 'ratio']).sort_values(['prefix', 'freq', 'ratio', 'suffix'],
                               ascending=[True, False, False, True])
bigramFreqTable['MED'] = 0
# end real word builder