from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import logging
from flask_sqlalchemy import SQLAlchemy
import urllib

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

#creating databasee

params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=IRFANEREN\SQLEXPRESS;"  
    "DATABASE=search_app_db;"        
    "UID=irfan;"             
    "Trusted_Connection=yes;"           
)

app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect={}".format(params)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

class SearchResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    def __init__(self, query, title, price, url):
        self.query = query
        self.title = title
        self.price = price
        self.url = url

# Creating the database tables 
with app.app_context():
    db.create_all()



@app.route('/')


def home():

    return render_template('index.html')

@app.route('/search', methods=['POST'])


def search():

    query = request.form['query']
    try:
        results = fetch_amazon_results(query)
        # here, we save results to database 
        for result in results:
            search_result = SearchResult(query=query, title=result['title'], price=result['price'], url=result['url'])
            db.session.add(search_result)
        db.session.commit()

        # returning index.html (home page template)
        return render_template('results.html', query=query, results=results)
    except Exception as e:
        logging.error(f"Error occurred during search: {e}", exc_info=True)
        return f"An error occurred: {e}", 500

# this function fetches results and showing to users on resluts page
def fetch_amazon_results(query):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    search_url = f"https://www.amazon.com.tr/s?k={query}"
    driver.get(search_url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".s-main-slot"))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    search_results = []

    items = soup.select(".s-main-slot .s-result-item")
    for item in items:
        title_element = item.select_one("h2 a span")
        price_whole = item.select_one(".a-price-whole")
        price_fraction = item.select_one(".a-price-fraction")
        link_element = item.select_one("h2 a")

        if title_element and price_whole and link_element:
            title = title_element.text
            price = f"{price_whole.text}.{price_fraction.text}" if price_fraction else price_whole.text
            link = f"https://www.amazon.com.tr{link_element['href']}"

            search_results.append({
                "title": title,
                "price": price,
                "url": link
            })


    #retuening results..
    return search_results




if __name__ == '__main__':
    app.run(debug=True)
