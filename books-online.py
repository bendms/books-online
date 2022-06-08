from bs4 import BeautifulSoup
import requests
import csv
from urllib.parse import urljoin

##### FONCTION POUR FAIRE UNE REQUETE GET POUR OBTENIR LE CODE HTML DE LA PAGE #####

def MakeTheSoup(url_livre):
    # url_website = url_livre
    html_livre = requests.get(url_livre).text
    soup = BeautifulSoup(html_livre, 'html.parser')
    return soup

##### FONCTION POUR TROUVER TOUTES LES CATEGORIES ET ENREGISTRER LES URLS DE CHAQUE CATEGORIE DANS UNE LISTE #####
def FindAllCategories(url, page):
    list_of_categories = []
    page = requests.get(url)
    #Parcourir la page
    soup = BeautifulSoup(page.text, 'html.parser')
    nav_list = soup.find(class_="nav nav-list").find_all("a", href = True)
    for a in nav_list:
        a = urljoin(url, a["href"])
        list_of_categories.append(a)
    list_of_categories.pop(0)
    return list_of_categories

##### FONCTION POUR SCRAPER LA PAGE D'UN LIVRE #####

def ScrapMyBook (url_livre, soup=None):
    #Pour chaque URL de liste livre, utiliser BeautifulSoup pour extraire les données et les stocker dans les listes
    tableau_livre = []
    html_livre = requests.get(url_livre).text
    soup_livre = BeautifulSoup(html_livre, 'html.parser')
  
    #URL Livre 
    product_page_url = url_livre

    #Title
    title = soup_livre.find(class_="col-sm-6 product_main")
    title = title.find('h1').string

    #Category
    list_a = []
    for a_href in soup_livre.find_all("a"):
        list_a.append(a_href.string)
    category = list_a[3]
    
    #Description
    description_class_search = soup_livre.find(class_="product_page")
    children_product_page = description_class_search.findChildren('p', recursive = False)
    description_livre_clean_tag = str(children_product_page).replace("<p>", "")
    product_description = str(description_livre_clean_tag).replace("</p>", "")

    #Review_rating 
    review_livre = soup_livre.find(class_="col-sm-6 product_main")
    children_review_livre = review_livre.find(class_="star-rating", recursive = False)
    children_review_livre.clear()
    children_review_livre_2 = str(children_review_livre).replace('<p class="star-rating ', "")
    review_rating = children_review_livre_2.replace('"></p>', "")

    #Extraction des données du tableau (UPC, Price excluding taxe, Price including tax, Number available)
    for td in soup_livre.find_all('td'):
        tableau_livre.append(td.string)
    universal_product_code = tableau_livre[0]
    price_excluding_tax = tableau_livre[2]
    price_including_tax = tableau_livre[3]
    number_available = tableau_livre[5]

    #Extraction de l'URL de l'image
    image_livre = soup_livre.select("div img")
    image_url = url_livre + image_livre[0]["src"]
    download_image = requests.get(image_url).content
    
    with open("test_img.jpg", "wb") as handler:
        handler.write(download_image)

    informations_livre = [product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax, product_description, category, review_rating, image_url]
    
    return informations_livre, category

##### VÉRIFIER SI LA PAGE EN COURS POSSÈDE UN BOUTON PAGE SUIVANTE ET RÉCUPÉRER LE CONTENU DE CETTE BALISE #####

def CheckNextPage(page):  
    page_content = BeautifulSoup(page.text, "html.parser")
    next_link = page_content.find(class_ = "next")
    if next_link != None:
        for a in next_link.find_all("a", href = True):
            next_page = a["href"]
        next_page_content = str(next_page).replace('<a href="', "").replace('">next</a>', "")
    else:
        next_page_content = "404"
    return next_page_content

##### FONCTION POUR CREER UN FICHIER CSV AVEC LE NOM DE LA CATEGORIE, Y AJOUTER LES ENTETES ET ECRIRE LES INFORMATIONS DANS LE FICHIER ###

def WriteInCsv (entetes, category, all_books_informations):
    file_name = str(category)
    #Créer une liste avec les entêtes suivantes : [”product_page_url”, “universal_ product_code (upc)”, “title, price_including_tax”, “price_excluding_tax”, “product_description”, “category”, “review_rating”, “image_url”]
    # entetes = ["product_page_url", "universal_product_code (upc)", "title", "price_including_tax", "price_excluding_tax", "product_description", "category", "review_rating", "image_url"]
    liste_csv = []        
    liste_csv.append(entetes)
    for informations_livre in all_books_informations:
        if informations_livre[6] == category:
            liste_csv.append(informations_livre)
    print(liste_csv)
    #Ouvrir un fichier CSV, y importer les entêtes et les informations dans des colonnes différentes
    with open(file_name + '.csv', 'a', encoding='UTF-8', newline = "") as f:
        writer = csv.writer(f)
        writer.writerows(liste_csv)

##### FAIRE LA LISTE DES LIVRES SUR LA PAGE #####

def FindAllBooks(url, page):
    links = []
    while page.ok:
        page = requests.get(url)
        #Parcourir la page
        soup = BeautifulSoup(page.text, 'html.parser')
        product_pods = soup.find_all(class_="product_pod")
        for product_pod in product_pods:
            a = product_pod.find("a")
            link = urljoin(url, a["href"])
            links.append(link)
            with open('liste_livres.txt', 'w', encoding='UTF-8') as f:
                writer = csv.writer(f)
                writer.writerow(links)
                print("Nombre de livre trouvés : " + str(len(links)))
        next_page_content = CheckNextPage(page)
        url = urljoin(url, next_page_content)
    return links


url = "http://books.toscrape.com/catalogue/category/books_1/index.html"
categories = []
links = [] 
all_books_informations = []
list_of_all_books_informations = []
page = requests.get(url)
categories = FindAllCategories(url, page)
i = 0
for category in categories:
    links = FindAllBooks(category, page)
    for link in links:
        informations_livre, category = ScrapMyBook(link)
        all_books_informations.append(informations_livre)
        list_of_all_books_informations.append(all_books_informations)
        # all_links.append(links)
        entetes = ["product_page_url", "universal_product_code (upc)" , "title", "price_including_tax", "price_excluding_tax", "product_description", "category", "review_rating", "image_url"]
    WriteInCsv(entetes, category, list_of_all_books_informations[i])
    i = i + 1

    
