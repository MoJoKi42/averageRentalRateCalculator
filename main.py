import requests
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass



# Hier den Link von der ERSTEN ebay-Kleinanzeigen Seite einfügen (Seite 1).
# Geht aktuell nur für Mietwohnungen!
url = "https://www.ebay-kleinanzeigen.de/s-wohnung-mieten/karlsruhe/wohnung/k0c203l9186r20"

# Preislimits
# Alles was außerhalb der Limits liegt, wird bei der Berechnung nicht berücksichtigt
price_limit_top =       40  # €/m²
price_limit_bottom =    4   # €/m²
space_limit_top =       200 # m²
space_limit_bottom =    0  # m²








def shrink_txt(txt):
    txt = str(txt)
    txt = txt.replace("\n", "") # remove \n
    txt_new = ""
    remove_chars = 0
    for i in range(0, len(txt)): # remove <....>
        if txt[i] == "<":
            remove_chars = remove_chars + 1
        if txt[i] == ">":
            remove_chars = remove_chars - 1
            if remove_chars < 0:
                remove_chars = 0
        if txt[i] != "<" and txt[i] != ">" and not remove_chars:
            txt_new = txt_new + txt[i]
    return txt_new

def str_to_float(str):
    str_new = ""
    for i in range(0, len(str)):
        if str[i] in "0123456789,.":
            str_new = str_new + str[i]
    str_new = str_new.replace(".", "")
    str_new = str_new.replace(",", ".")
    try:
        return float(str_new)
    except:
        return 0.0

err_cnt_scraping = 0
err_cnt_pricelimit = 0
wohnungsliste = []
for page_num in range(1, 50):

    if(len(wohnungsliste) == 0):
        print("processing page:", end="", flush=True)
    print(" " + str(page_num), end="", flush=True)

    # URL bestimmen
    urls = url.split("/wohnung/")
    url_new = urls[0] + "/seite:" + str(page_num) + "/wohnung/" + urls[1]

    # Daten scrapen
    header = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    content = requests.get(url_new, headers=header).text
    soup = BeautifulSoup(content, "html.parser")
    navigation = soup.findAll("div", {"class": "pagination-nav"})
    if(len(navigation) == 1 and page_num != 1):
        print("\n", end="", flush=True)
        break

    # Angebotliste extrahieren (von aktueller Seite)
    table =     soup.findAll("ul", {"id": "srchrslt-adtable"})
    ads =   table[0].findAll("article", class_="aditem")

    # Alle Angebote durchgehen (von aktueller Seite)
    for i in range(0, len(ads)):
        try:
            price = ads[i].find("p",        {"class": "aditem-main--middle--price-shipping--price"})
            price = str_to_float(shrink_txt(price))
            temp = ads[i].findAll("span",   {"class": "simpletag tag-small"})
            space = str_to_float(shrink_txt(temp[0]))
            rooms = str_to_float(shrink_txt(temp[1]))

            flat = {}
            flat["price"] = price
            flat["space"] = space
            flat["rooms"] = rooms
            wohnungsliste.append(flat)
        except:
            err_cnt_scraping = err_cnt_scraping + 1
            #print("skipped one ad! (scraping error)")


#  Durchschnitt berechnen
price_sum = 0
price_list = []
price_count = 0
for i in range(0, len(wohnungsliste)):
    price = wohnungsliste[i]["price"]
    space = wohnungsliste[i]["space"]

    try:
        price_per_space = (price/space)
    except:
        price_per_space = 9999

    if(not(price_per_space > price_limit_top or price_per_space < price_limit_bottom
         or space > space_limit_top or space < space_limit_bottom)):
        price_sum = price_sum + price_per_space
        price_count = price_count + 1
        price_list.append(price_per_space)
        #print(str(price_per_space) + "€/m²")
    else:
        err_cnt_pricelimit = err_cnt_pricelimit + 1
        #print("skipped one ad! (out of limit " + str(price_per_space) + " €/m²")


print("skipped " + str(err_cnt_scraping) + " ads due scraping errors!")
print("skipped " + str(err_cnt_pricelimit) + " ads due price/space limit violations!")
print("found " + str(price_count + err_cnt_scraping + err_cnt_pricelimit) + " ads in total ", end="")
print("and used " + str(price_count) + " ads for calculating!")

print("\nAverage price: ", end="", flush=True)
print("%.2f €/m²" %(price_sum/price_count))

price_list.sort()
median = price_list[int(len(price_list)/2)]
print("Median price:  ", end="", flush=True)
print("%.2f €/m²" %(median))
