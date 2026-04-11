# | First release: March 18th, 2026
# | Last update..: March 18th, 2026
# | WhatIs.......: Web Scraping Walmart - Main
# | Author.......: Juan Pablo Quezada Jimenez
# +----------------------------------------------------------------------------++
# ------------------------- Instructions -----------------------
# TODO:

# ------------ Resources / Documentation involved -------------
# The Translator in Your Computer: https://cpu.land/the-translator-in-your-computer

# ------------------------- Libraries -------------------------
from playwright.sync_api import sync_playwright
import re
import datetime
from bs4 import BeautifulSoup
import requests
import pandas as pd
#send emails import
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ------------------------- Functions -------------------------
class DataSearcher:
    def __init__(self, url, headers):
        self.url = url
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers
            
        if not self.url.startswith("http"):
            self.url = "https://"+self.url
            
    def get_data(self, prices_selector_css, name_selector_css, show_website_data=False, show_value=False):
        with sync_playwright() as p:
            #set up a fake profile in Edge
            user_data_dir = "./perfil_falso_chrome"
            browser=p.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                channel="msedge", 
                args=["--disable-blink-features=AutomationControlled"],
                viewport=None
                )
            page=browser.pages[0]
            #stealth_sync(page)
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: ()=>undefined})")
            page.set_extra_http_headers(self.headers)
            page.goto(self.url)
            page.wait_for_timeout(5000)
            #response=requests.get(self.url, headers=self.headers)
            website_html = page.content()
            if show_website_data:
                print(website_html)
            #soup = BeautifulSoup(website_html, "html.parser")
            try:
                #value=soup.find_all(name=tag_name, attrs=attrs)[0].get_text()
                value=[page.locator(prices_selector_css).first.inner_text(),page.locator(name_selector_css).first.inner_text()]
                if show_value:
                    if value == '':
                        print("Empty Value")
                    else:
                        print(f"value: {value}")
                browser.close()
                return value
            except Exception as e:
                if show_value:
                    print(f"Tag not found: {prices_selector_css}. Error: {e}")
                browser.close()
                return ''


# ------------------------- Variables -------------------------
# Time
now = datetime.datetime.now()
todayDate = now.strftime("%d/%m/%y")
todayTime = now.strftime("%H:%M")

emailSubject = f"This is a test {todayDate} at {todayTime}"



records_folder = 'records'
ipad_FileName = 'ipad_PriceTracker.csv'
records_path = f'{records_folder}/{ipad_FileName}'

URL_WALMART = ("https://www.walmart.com.mx/ip/ipad-8th-apple-10-2-pulgadas-32gb-plata-reacondicionado/00075976331902?athbdg=L1300&from=/search")

HEADERS_WALMART = {
    "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

URL_AMAZON = ("https://www.amazon.com.mx/Apple-iPad-10-Wi-Fi-generación/dp/B08KWJW3DV/ref=asc_df_B08KWJW3DV?mcid=807e7402d13b34d1af1a02ed7333e055&tag=gledskshopmx-20&linkCode=df0&hvadid=709966298345&hvpos=&hvnetw=g&hvrand=266207028048084159&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9222637&hvtargid=pla-1996733853277&psc=1&hvocijid=266207028048084159-B08KWJW3DV-&hvexpln=0&language=es_MX")

HEADERS_AMAZON={
    "Accept-Language":"en-US,en,;q=0.9",
    "User-Agent":"CCBot/2.0 (https://commoncrawl.org/faq/)"
}
# --------------------------- Code ----------------------------

Path(f'{records_folder}').mkdir(parents=True,exist_ok=True)

webData_walmart=DataSearcher(url=URL_WALMART, headers=HEADERS_WALMART)
webData_amazon=DataSearcher(url=URL_AMAZON, headers=HEADERS_AMAZON)
info_amazon= webData_amazon.get_data(prices_selector_css='.a-price-whole',name_selector_css='.a-size-large.product-title-word-break', show_website_data=True)
info_walmart = webData_walmart.get_data(prices_selector_css='span[data-seo-id="hero-price"]',name_selector_css='.dark-gray.mv1.lh-copy.f3.mh0.b',show_website_data=True)
if info_walmart != '':
    info_walmart[0] = float(re.sub(r'[,\n\r\$]', '', info_walmart[0]))
    print(f"price walmart: {info_walmart}")
else:
    print("No price found")


if info_amazon != '':
    info_amazon[0] = float(re.sub(r'[,\n\r\$]', '', info_amazon[0]))
    print(f"price amazon:  {info_amazon}")
else:
    print("No price found")
    


new_records = {
    "datetime" : [pd.Timestamp.now(), pd.Timestamp.now()],
    "Provider" : ["Walmart", "Amazon"],
    "Name" : [info_walmart[0], info_amazon[0]],
    "price" : [info_walmart[1], info_amazon[1]]
}

records_DataFrame = []
new_rows=pd.DataFrame(new_records)

try:
    records_DataFrame = pd.read_csv(records_path)
    records_DataFrame = pd.concat([records_DataFrame, new_rows], ignore_index=True)
    records_DataFrame.to_csv(records_path, index=False)
    print("File's data successfully updated")
except FileNotFoundError or IndexError:
    print(f"File not found. Creating CSV at {records_folder}")
    records_DataFrame = pd.DataFrame(new_records)
    records_DataFrame.to_csv(records_path, index=False)
    print("File successfully created")
    
allTime_lowestPrice = records_DataFrame.loc[records_DataFrame['price'].idxmin()]
print(f"\nAll time lowest price: \n{allTime_lowestPrice}")

today_lowestPrice = new_rows.loc[new_rows['price'].idxmin()]
print(f"\nToday lowest price: \n{today_lowestPrice}")

if today_lowestPrice['price'] < allTime_lowestPrice['price']:
    conclusion = 'This is a record <span class="good">You should buy</span> your product today'
    print(f"\nThis is a record, ${today_lowestPrice['price']} Yo should buy your product today")
else:
    conclusion = 'Today is <span class="bad">not a good</span> day to buy your product'
    print(f"\nYour product's price today is: ${today_lowestPrice['price']}\nDifference aagainst record low price (${allTime_lowestPrice['price']}) is: ${today_lowestPrice['price']-allTime_lowestPrice['price']}")
    
email_body = f'''
<html>
    <head>
        <style>
            .amazon {{
                color: #FF9900;
                font-weight: bold;
                text-decoration: none;
            }}
            .tymo {{
                color: #AC2A45;
                font-weight: bold;
                text-decoration: none;
            }}
            .good {{
                color: #32CD32;
                font-weight: bold;
            }}
            .bad {{
                color: #FF7034;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>AMAZON Curl Pro Plus</h1>
        <h2>Today prices</h2>
        <p>Price <a href="{URL_WALMART}" class="amazon" target="_blank">Amazon</a>: ${info_walmart[0]} MXN</p>
        <p>Price <a href="{URL_AMAZON}" class="tymo" target="_blank">Tymo</a>: ${info_amazon[0]} MXN</p>
        <h2>Record</h2>
        <p><b>All time Lowest Price:</b> ${allTime_lowestPrice['price']} ({allTime_lowestPrice['provider']} - {allTime_lowestPrice['datetime']})</p>
        <p><b>Today Lowest Price:</b> ${today_lowestPrice['price']} ({today_lowestPrice['provider']} - {today_lowestPrice['datetime']})</p>
        <p>Difference against record low price (${allTime_lowestPrice['price']}) is: ${today_lowestPrice['price'] - allTime_lowestPrice['price']}</p>
        <h2>Conclusion</h2>
        <p>{conclusion}</p>
    </body>
</html>
'''
print(email_body)
email = MIMEMultipart('alternative')
email['Subject'] = emailSubject
email['From'] = botEmail
email['To'] = myEmail

HTMLPart=MIMEText(email_body, 'html')

email.attach(HTMLPart)
print(email.as_string())

connection = smtplib.SMTP("smtp.gmail.com",587)
connection.login(user=botEmail, password=botPassword)
connection.sendmail(from_addr=botEmail, to_addrs=myEmail,msg=email.as_string())
connection.close()
print("Email sent successfully")



