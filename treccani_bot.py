# Author Tommaso Macchioni 2020
import os
import requests
import urllib.request
import re
from bs4 import BeautifulSoup
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from time import sleep

#!!!! Insert here your TOKEN !!!!
BOT_TOKEN = os.environ.get('BOT_TOKEN')

update_id = None


def start(update, context):
    update.message.reply_text('Ciao! Inviami un vocabolo e ti restituisco la definizione della Treccani.')

def echo(update, context):
    chat_id = update.message.chat_id
    #print('\n',update["message"]["chat"]["first_name"],update["message"]["chat"]["last_name"],update["message"]["chat"]["username"],update["message"]["text"])    

    try:
        parola = update.message.text.lower()
        parola = parola.replace(" ","-")
        i = 0
        more_than_one = False

        while(True):
            if (more_than_one == False):
                url = "http://www.treccani.it/vocabolario/" + parola
            else:
                url = "http://www.treccani.it/vocabolario/" + parola + str(i)


            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            try:
                text_spiega = str(soup.find("div", {"class": "text spiega"}).find("p"))
            except(AttributeError):
                if(more_than_one == False):
                    i += 1
                    url = "http://www.treccani.it/vocabolario/" + parola + str(i)
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, "html.parser")
                    try:
                        text_spiega = str(soup.find("div", {"class": "text spiega"}).find("p"))
                        more_than_one = True
                    except(AttributeError):
                        context.bot.send_message(chat_id=chat_id, text="<b>Errore:</b> <i>vocabolo non trovato</i>", parse_mode=telegram.ParseMode.HTML)
                        #print("Errore: vocabolo non trovato")
                        break
                else:
                    break

            text_spiega = re.sub("<p>|</p>", "", text_spiega)
            text_spiega = re.sub("<!-- .* -->", "", text_spiega)

            for span in soup.findAll("span"):
                span = str(span.unwrap())
                span = re.sub("</span>", "", span)
                text_spiega = re.sub(span, "", text_spiega)

            text_spiega = re.sub('</span>', "", text_spiega)

            for annot in soup.findAll("annotation"):
                annot = str(annot.unwrap())
                annot = re.sub("</annotation>", "", annot)
                text_spiega = re.sub(annot, "", text_spiega)

            text_spiega = re.sub('</annotation>', "", text_spiega)

            text_spiega = re.sub("<sup>", " ", text_spiega)
            text_spiega = re.sub("</sup>", "", text_spiega)


            if (len(text_spiega) <= 4096):
                context.bot.send_message(chat_id=chat_id, text=text_spiega, parse_mode=telegram.ParseMode.HTML)
            else:
                buf = ""
                removed = ""
                for portion in text_spiega.split(' '):
                    if((len(buf)+len(removed)+len(portion)) <= 4096):
                        buf += portion + " "
                    else:
                        while(True):
                            try:
                                context.bot.send_message(chat_id=chat_id, text=buf, parse_mode=telegram.ParseMode.HTML)
                                break
                            except:
                                min_occ = buf.rfind(r'<')
                                removed = buf[min_occ:] + removed
                                buf = buf[0:min_occ]
                        buf = removed + portion + " "
                        removed = ""

                context.bot.send_message(chat_id=chat_id, text=buf, parse_mode=telegram.ParseMode.HTML)

            if(more_than_one == False):
                break
            else:
                i+=1

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /search <word>')


def main():
    
    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(MessageHandler(Filters.text, echo))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
