# coding: utf-8
#translate_summary_field
#Author: Killo3967
#Description: This script translate the "Summary" field of the comic using Google Translate 
#Versions: 1.0  
#
#@Name  Translate Summary Field with Google
#@Hook  Books
#@Key   Translate Summary Field with Google
#@Image translate_summary_field.png

import clr
import sys

clr.AddReference('System')
from System.IO import File, StreamReader, StreamWriter, StringWriter
from System.Text import Encoding
from System.Net import HttpStatusCode, WebException, WebRequest
from System.Net import ServicePointManager, SecurityProtocolType

clr.AddReference('System.Web')
from System.Web import HttpUtility

import json 
import time
import re

# Setting Variables
global debug, target_lang, separator_chars
debug = True

# Define staticaly the target lang
target_lang = ""

# Define the separator chars 
separator_chars = ['.', '?', '!', '\n']
# Define the exceptions
no_separator_chars_pattern1 = r"(\w+\.\s?'\w)"
# Define illegal chars (to replace by space)
illegal_chars = ['<', '>']

# Time delays (in seconds)
delay_between_sentences = 0.15
delay_between_comics = 1

# Get locale data to obtain the target language.
import locale
# If not staticaly defined the source language y try to get it.
if target_lang == "":
    target_lang = str(locale.getdefaultlocale()).strip("()'").split(',',1)[0].split('_',1)[0]

print ("+++++++++++++    SYSTEM INFO     ++++++++++++++++")
print (">>>>> EXECUTABLE: " + str(sys.executable))
print (">>>>> VERSION: " + str(sys.version))
print (">>>>> PLATFORM: " + str(sys.platform))
print (">>>>> CODE PAGE: " + str(sys.getdefaultencoding()))
print (">>>>> DETECTED LANGUAGE: " + target_lang)
for p in sys.path:
    print (">>>>> PATH: " + p)
print ("+++++++++++++++++++++++++++++++++++++++++++++++++")

def translate_summary_field(books):
    if books.Length == 0:
        print("No comics have been selected. Exiting.")
        exit
    print(" ")
    print("     <<<<<<<< START SUMMARY FIELD TRANSLATION >>>>>>>>>>")

    # Main Loop
    for book in books:
        if debug: print("")
        if debug: print(">> Processing comic: " + unicode(book.FilePath))   # unicode = str
        v_summary = ""
        v_summary = (book.Summary).strip()

        # If Summary has data
        if v_summary:
            if debug: 
                print("Summary for translate: " + v_summary)
                print ("  ----------")
            
            # Replace the "." in certain patterns like "Bob. 's", before splitting.
            matches = re.findall(no_separator_chars_pattern1, v_summary)
            if matches:
                for match in matches:
                    v_summary = v_summary.replace(match, match.replace(".", ""))

            # Split the summary into individual sentences for better translations (by Google).
            sentences = []
            sentence = ""
            for char in v_summary:
                if char in separator_chars:
                    sentence += char
                    if char == '.':
                        sentences.append(sentence)
                    elif char == '?':
                        sentences.append('?' + sentence)
                    elif char == '!':
                        sentences.append('!' + sentence)
                    elif char == '\n':
                        sentences.append('\n' + sentence)
                    sentence = ""
                else:
                    sentence += char

                # Time delay between sencences
                # time.sleep(delay_between_sentences)
            
            if sentence:
                sentences.append(sentence)
        
            # Translate each sentence and join them back together
            translated_sentences = []
            for sentence in sentences:
                
                # Chech CR/LF at start and at end before translations and before cleaning
                start_chars=''
                end_chars=''
                if sentence.startswith('\n\r') or sentence.startswith('\r\n'):
                    start_chars = '\r\n'
                if sentence.endswith('\n\r') or sentence.endswith('\r\n'):
                    end_chars = '\r\n'
                if sentence.startswith('\n'):
                    start_chars = '\r\n'
                if sentence.endswith('\n'):
                    end_chars = '\r\n'
                
                # Now i could clean and translate
                c_sentence = sentence_clean(sentence)
                sentence=c_sentence
                if sentence:
                    if debug: print("   >>Sentence for translate: " + sentence)
                    # NOW Translate without non ascii characters
                    translated_sentence = google_translate_text(sentence)

                    # And now, after translate, recover the CRLF
                    if start_chars is not None or end_chars is not None:
                        translated_sentence = start_chars + translated_sentence + end_chars
                    if debug: 
                        print("   >>Translated sentence: " + translated_sentence)
                        print ("  ----------")
                    # translated_sentence = translated_sentence.rstrip('\r\n')
                    
                    # Add delay time
                    # time.sleep(delay_between_sentences)
                    
                    # Add the output to the list
                    translated_sentences.append(translated_sentence)
        
            translated_text = ' '.join(translated_sentences)
            if debug: print("Translated Summary: " + translated_text)
            # Replace summary field with translated version 
            book.Summary = translated_text
            # Add a custom value for information, and for create smart list.
            book.SetCustomValue("Summary_translated",target_lang)
            
            # Add a delay time between comic books
            # time.sleep(delay_between_comics)
        else:
            if debug: print("Summary field empty, nothing to traslate.")
    print("")
    print("     <<<<<<<< FINISH TRANSLATIONS >>>>>>>>>>")


# ComicVine sometimes returns rare characters in the text. 
# It's necessary prepare the text, before send to Google. 
def sentence_clean(text):
    text = text.strip()
    if text.startswith('?'):
        text = text[1:]
    text = text.replace("<","'")
    text = text.replace(">","'")
    text = text.replace("\n","")
    text = text.replace("\r","")
    text = text.replace("\t","")
    return text


# Call Google for a string translation and process the response
def google_translate_text(text):
    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={}&dt=t&q={}'.format(target_lang, text)
    response = get_html_string(url)
    response_text = strip_invalid_chars(response)
    clean_text = json.loads(response_text)
    translated_text = clean_text[0][0][0]
    return translated_text
    
# Web Request, GET method. 
def get_html_string(url):
   try:
      ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12
      request = WebRequest.Create(url)
      
      request.UserAgent = "Comic Translator"
      response = request.GetResponse()
      
      if response.StatusCode != HttpStatusCode.OK:
         raise WebException("server response code " + sstr(int(response.StatusCode))+" ("+sstr(response.StatusCode)+")" )
      responseStream = response.GetResponseStream()
      reader = StreamReader(responseStream, Encoding.UTF8)
      page = reader.ReadToEnd()
      with StringWriter() as writer: 
         HttpUtility.HtmlDecode(page, writer)
         page = writer.ToString()
      return page
   finally:
      if 'reader' in vars(): reader.Close()
      if 'responseStream' in vars(): responseStream.Close()
      if 'response' in vars(): response.Close()


# Safely converts the given object into a string (sstr = safestr)
# this is needed, because str() breaks on some strings that have unicode
# characters, due to a python bug.  (all strings in python are unicode.)
def sstr(object):
   if object is None:
      return '<None>'
   if is_string(object):
      return object 
   return str(object)

# Delete unwanted characters
def strip_invalid_chars(text):
   def is_valid(c):
      return c == 0x9 or c == 0xA or c == 0xD or\
         (c >= 0x20 and c <= 0xD7FF) or\
         (c >= 0xE000 and c <= 0xFFFD) or\
         (c >= 0x10000 and c <= 0x10FFFF)

   if text:
      text = ''.join([c for c in text if is_valid(ord(c))])
   return text


# Not in use now, For future implementation
def obtain_locale():
    available_locales = []
    for l in locale.locale_alias.items():
      try:
        locale.setlocale(locale.LC_ALL, l[1])
        available_locales.append(l)
      except:
        pass
