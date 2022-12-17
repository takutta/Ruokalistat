# -*-coding: utf-8 -*-
from flask import Flask, render_template, request, session, url_for, redirect
from livereload import Server
import random, feedparser, re, sys, json, io, datetime
from babel.dates import format_date, format_datetime, format_time
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.debug = True
app.secret_key = os.urandom(12)

#print('4', file=sys.stderr)

# todo: 
# - Päivät suomeksi
# - ['Viikot peräkkäin', 'viikot vierekkäin', 'viikot vierekkäin 2 paperille']
# - Koulujen lisäys (tai eri kategorioiden ylipäätään)
# - ical -osoitteen lisäys

@app.route('/')
def base_page():
    paivakodit = listaus()
    return render_template(
		'alku.html', paivakodit=paivakodit
	)

@app.route('/pk/<nimi>_<ruoat>_<viikkoja>_<jarjestys>')
def valittu(nimi:str, ruoat:str, viikkoja:int, jarjestys:str):
    paivakodit = listaus()
    menu = listan_luonti(nimi, ruoat, viikkoja)
    viikot = []
    paivat = []
    vierekkain = False
    vierekkain2 = False
    if jarjestys == "vierekkain":
        vierekkain = True
    elif jarjestys == "vierekkain2":
        vierekkain2 = True
    for dict in paivakodit:
        for key, value in dict.items():
            if value == nimi:
                paivakoti = dict['Nimi']
    
    for viikko in menu:
        eka_paiva = list(viikko.keys())[0]
        eka_paiva = datetime.datetime.strptime(eka_paiva, "%d.%m.%Y")
        eka_paiva = eka_paiva.strftime('%U')
        viikot.append(eka_paiva)
        for paiva, ruoka in viikko.items():
            pv = format_date(datetime.datetime.strptime(paiva, "%d.%m.%Y"), 'EEE', locale='fi_FI')
            #pv = pv.strftime('%a')
            paivat.append(pv)
    return render_template('paivakoti.html', menu = menu, print = True, viikot = viikot, paivat = paivat, paivakoti = paivakoti, viikkoja = viikot[int(viikkoja)-1], vierekkain = vierekkain, vierekkain2 = vierekkain2
    )

@app.route('/paivakoti',methods = ['POST', 'GET'])
def paivakoti():
    if request.method == 'POST':
        valinta = request.form.get('paivakoti')       
        ruoat = request.form.get('ruoat')
        jarjestys = request.form.get('jarjestys')
        viikkoja = request.form.get('viikot')
        
        return redirect(url_for('valittu',nimi = valinta, ruoat = ruoat, jarjestys = jarjestys, viikkoja = viikkoja)
        )

def rss_haku(Nimi: str, viikko:int):
    lista = listaus()
    Konenimi = ''
    ID = ''
    for pk in lista:
        if Nimi == pk['Konenimi']:
            ID = pk['ID']
            break
    Rss = feedparser.parse("http://aromimenu.cgisaas.fi/JyvaskylaAromieMenus/fi-FI/Default/Ravintola/" + Nimi + "/Rss.aspx?Id=" + ID + "&DateMode=" + str(viikko))   
    return Rss.entries

def viikon_lista(rss: list, kummat: str):
    paivaruoat = ['Aamupala', 'Lounas', 'Välipala', 'Kasvislounas']
    iltaruoat = ['Päivällinen', 'Iltapala']
    paivan_ruoat = []
    ruoat = {} # päivän ruoat
    menu = {}
    for dict in rss:
        ruoat = {}
        paivan_ruoat = dict["summary"].split("<br />")        
        for ruoka in paivan_ruoat:
            
            tyhja_haku = ruoka.find(' ')  # Ruokailun nimi            
            ruokailu = ruoka[:tyhja_haku-1] 
            ateria = ruoka[tyhja_haku+1:]
            ateria = re.sub("[\(\[].*?[\)\]]", ",", ateria) # Poistetaan sulkeet
            ateria = ateria.split(",") # Erotellaan ainesosat listaksi
            ateria = list(filter(None, ateria)) # Poistetaan tyhjat itemit
            ateria = [x.strip(' ') for x in ateria] # Poistetaan valilyonnit
            ateria = [x.lower() for x in ateria] # Lowercase
            
            # Tehdaan dict, avaimena ruokailun nimi
            # Mitkä ruokailut otetaan mukaan 
            if kummat == "paiva":
                if ruokailu in paivaruoat:
                    if ruokailu == "Kasvislounas":
                        ruoat['Lounas'].append(ateria[0])
                    else:
                        ruoat[ruokailu] = ateria
            elif kummat == "ilta":
                if ruokailu in iltaruoat:                    
                    ruoat[ruokailu] = ateria
            elif kummat == "paivailta":
                if ruokailu == "Kasvislounas":
                    ruoat['Lounas'] += ateria
                else:
                    ruoat[ruokailu] = ateria

        # päivän ateriat
        menu[dict['title'][3:]] = ruoat
                  
    return menu

def listan_luonti(nimi:str, ruoat:str, viikot:int):
    lista = []
    for i in range(1, int(viikot)+1):
        entries = rss_haku(nimi, i)        
        lista.append(viikon_lista(entries, ruoat))
    return lista

def listaus ():
    return json.load(open('paivakodit.json', encoding="utf-8"))   

if __name__ == "__main__":
    if os.environ.get("FLASK_ENV") == "production":
        app.run(debug=False, host='0.0.0.0', port=8080)
    else:
        app.debug = True
        server = Server(app.wsgi_app)
        server.serve()