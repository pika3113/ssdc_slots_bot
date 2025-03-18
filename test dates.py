from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import visibility_of_element_located
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import datetime
import time
import os
import sys
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import html, json, logging, os,\
       telegram as tg,\
       telegram.constants as tgc,\
       telegram.ext as tge
from zoneinfo import ZoneInfo
import logging

def is_date_equal_or_within_ten_days_ahead(date_str2):
    date1 = datetime.datetime.now()
    date2 = datetime.datetime.strptime(date_str2, "%d %b %Y")
    ten_days_ahead = date1 + datetime.timedelta(days=10)
    return date1.date() <= date2.date() <= ten_days_ahead.date()

sent = {}

async def scheduled_task(context: tge.CallbackContext):
    lst = ["Basic Theory Test",'Final Theory Test','Riding Theory Test','Class 2B 1st Attempt','Class 2B Re-test','Class 2A 1st Attempt','Class 2A Re-test','Class 2 1st Attempt','Class 2 Re-test','Class 3 1st Attempt','Class 3 Re-test','Class 3a 1st Attempt','Class 3a Re-test','Class 3/3A(PDI Students) 1st Attempt','Class 3/3A(PDI Students) Re-test','Class 4 1st Attempt','Class 4 Re-test','Class 5 1st Attempt','Class 5 Re-test']
    all_date_cells = []
    new = []
    old = []

    chrome_options = Options()
    chrome_options.add_argument("--start-minimized")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    browser = webdriver.Chrome(options=chrome_options)
    browser.minimize_window()
    browser.get("https://ssdcl.com.sg/test-dates")  # navigate to URL
    content = browser.page_source
    browser.close()

    service = Service("C:\\Users\\pika\\Documents\\chromedriver-win64\\chromedriver.exe")
    service.log_output = None

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, "html.parser")
    html = soup.text

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.txt"
    entrydetails = soup.find("div", class_="entry-details")
    if entrydetails:
        tablepress_wrappers = entrydetails.find_all("div", class_="tablepress-scroll-wrapper")

    for w in tablepress_wrappers:
        all_date_cells.extend(w.select("td.column-2.text-center.nowrap"))

    for cell in all_date_cells:
        date_str = cell.get_text(strip=True)
        new.append(date_str)
    new = new[::2]

    # with open("testdatatest.json",'r') as file:
    #     for i in file:
    #         new.append(i.strip())

    with open('testdata.json','r') as file:
        for i in file:
            old.append(i.strip())

    chat_id = "-1002293836638"
    message_id = 32
    for k, (i, j) in enumerate(zip(old, new)):
        if i != j:
            print(f'New date for {lst[k]} on {j}')
            if is_date_equal_or_within_ten_days_ahead(j):
                message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=f'New date for {lst[k]} on <b>{j}</b>',
                    parse_mode='HTML'
                )
                message_idd = message.message_id
                sent[j] = [k,message_idd]
            
            with open('testdata.json','w') as file:
                for i in new:
                    file.write(i + "\n")

            #edit msg
            rows = ""
            for i, k in enumerate(new[:3]):
                rows += f"{lst[i]} | <b>{k}</b>\n"
            tt_final = f"🏫 <b>Theory Test</b>\n{rows}"

            rows = ""
            c = 0
            for i, k in enumerate(new[3:]):
                c+=1
                rows += f"{lst[i+3]} | <b>{k}</b>\n"
                if c==2:
                    rows+='\n'
                    c=0
            ft_final = f"🚗 <b>Practical Test</b>\n{rows}"

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=tt_final + '\n\n' + ft_final,
                parse_mode='HTML'
            )

    for i,j in sent.items():
        k = j[0]
        j=j[1]
        if new[k] != i:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=j
            )
            del sent[i]
    
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=59,
        text='lastupdate: '+current_time+' '+current_date,
        parse_mode='HTML'
    )
        

def main() -> None:
    """Start the bot."""
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))  # Get the directory where the script is
    os.chdir(script_dir)
    with open("bot_keys.json") as fp:
        application = tge.Application.builder().token(
            json.load(fp)["testdate"]
            ).defaults(
                tge.Defaults(
                    parse_mode=tgc.ParseMode.HTML,
                    tzinfo=ZoneInfo("Asia/Singapore")
                    )
                ).build()
    application.job_queue.run_repeating(scheduled_task, interval=30, first=0)
    application.run_polling()
    


if __name__ == "__main__":
    main()



