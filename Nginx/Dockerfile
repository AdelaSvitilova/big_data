#stáhni z dockerhubu tento základní obraz
FROM python

#vytvoř v obrazu pracovní adresář v rootu s názvem app a přesuň se do něj (kombinace mkdir a cd)
WORKDIR /app

#zkopíruj z mého pracovního adresáře na mém disku soubor requirements.txt se závislostmi pythonu a vlož ho do pracovního adresáře obrazu
COPY requirements.txt .

#spusť v obrazu správce balíku pip a nainstaluj závislost z requirements souboru
RUN pip install -r requirements.txt

#zkopíruj z mého pracovního adresáře na mém disku obsah složky src a zkopíruj ho do pracovního adresáře v obrazu (/app)
COPY src/ ./

#spusť přes příkazovou řádku naší flask aplikaci na adrese 0.0.0.0
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]