from bs4 import BeautifulSoup
import requests
import csv
from urllib.parse import urljoin
import re
import os

##### FONCTION POUR TROUVER TOUTES LES CATEGORIES ET ENREGISTRER LES URLS DE CHAQUE CATEGORIE DANS UNE LISTE #####

def find_all_categories(url, page):
    """Return all categories of books from website with ahref tags in HTML page

    Args:
        url (string): URL of website we want to scrap
        page (requests.models.Response): Status code for a HTTP request from server

    Returns:
        list_of_categories (list): list of all categories in the website
    """
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

def scrap_my_book (url_livre, soup=None):
    """Functions return list with all requested informations from specific book page and category of this books

    Args:
        url_livre (string): URL of website we want to scrap
        soup (bs4): Return soup object with informations from HTML page

    Returns:
        informations_livre (list): list of following informations from page : product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax, product_description, category, review_rating, image_url 
        category (string): string from which category this books belong
    """
    #Pour chaque URL de liste livre, utiliser BeautifulSoup pour extraire les données et les stocker dans les listes
    tableau_livre = []
    html_livre = requests.get(url_livre).content
    soup_livre = BeautifulSoup(html_livre, 'html.parser')
  
    #URL Livre 
    product_page_url = url_livre

    #Title
    title = soup_livre.find(class_="col-sm-6 product_main")
    title = title.find('h1').string
    title = str(title)

    #Category
    list_a = []
    for a_href in soup_livre.find_all("a"):
        list_a.append(a_href.string)
    category = list_a[3]
    
    #Description
    description_class_search = soup_livre.find(class_="product_page")
    children_product_page = description_class_search.findChildren('p', recursive = False)
    description_livre_clean_tag = str(children_product_page).replace("<p>", "")
    product_description_with_special_character = str(description_livre_clean_tag).replace("</p>", "")
    product_description = re.sub('[^\w \n\.]', '', product_description_with_special_character)

    #Review_rating 
    review_livre = soup_livre.find(class_="col-sm-6 product_main")
    children_review_livre = review_livre.find(class_="star-rating", recursive = False)
    children_review_livre.clear()
    children_review_livre_2 = str(children_review_livre).replace('<p class="star-rating ', "")
    review_rating = children_review_livre_2.replace('"></p>', "")

    #Extraction des données du tableau (UPC, Price excluding taxe, Price including tax)
    for td in soup_livre.find_all('td'):
        tableau_livre.append(td.string)
    universal_product_code = tableau_livre[0]
    price_excluding_tax = tableau_livre[2].replace("Â", "")
    price_including_tax = tableau_livre[3].replace("Â", "")
    
    #Extraction du nombre de produits disponibles (Number available)
    check_number_available = soup_livre.find(class_="instock availability").getText()
    check_space_before_number_available = check_number_available.replace("\n\n    \n        ", "")
    number_available = check_space_before_number_available.replace("\n    \n", "")

    #Extraction de l'URL de l'image
    image_livre = soup_livre.select("div img")
    image_url = urljoin(url_livre, image_livre[0]["src"])
    # image_url = url_livre + image_livre[0]["src"]
    download_image = requests.get(image_url).content

    informations_livre = [product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax, number_available, product_description, category, review_rating, image_url]
    
    name_my_image_without_special_characters = re.sub('[^\w \n\.]', '', title)
    
    if not os.path.exists("images"):
        os.makedirs("images")
    with open("images/" + name_my_image_without_special_characters + ".jpg", "wb+") as handler:
        handler.write(download_image)
    
        
    return informations_livre, category

##### VÉRIFIER SI LA PAGE EN COURS POSSÈDE UN BOUTON PAGE SUIVANTE ET RÉCUPÉRER LE CONTENU DE CETTE BALISE #####

def check_next_page(page):  
    """Check if there is a next page button / link from specific page with HTML tag

    Args:
        page (requests.models.Response): Status code for a HTTP request from server

    Returns:
        next_page_content (string): url of next page
    """
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

def write_in_csv (entetes, category, all_books_informations):
    """create a csv file and named it with category name, write informations of these books from a list and close the file

    Args:
        entetes (list): list of headers shown in csv file
        category (string): category of books we want to write in csv file, also string for naming the file
        all_books_informations (list): list of list of all books informations scrapped before
    """
    file_name = str(category)
    #Créer une liste avec les entêtes suivantes : [”product_page_url”, “universal_ product_code (upc)”, “title, price_including_tax”, “price_excluding_tax”, “product_description”, “category”, “review_rating”, “image_url”]
    # entetes = ["product_page_url", "universal_product_code (upc)", "title", "price_including_tax", "price_excluding_tax", "product_description", "category", "review_rating", "image_url"]
    liste_csv = []        
    liste_csv.append(entetes)
    for informations_livre in all_books_informations:
        if informations_livre[7] == category:
            liste_csv.append(informations_livre)
    if not os.path.exists("datas"):
        os.makedirs("datas")
    #Ouvrir un fichier CSV, y importer les entêtes et les informations dans des colonnes différentes
    with open("datas/" + file_name + '.csv', 'w', encoding='UTF-8', newline = "") as f:
        writer = csv.writer(f)
        writer.writerows(liste_csv)

##### FAIRE LA LISTE DES LIVRES SUR LA PAGE #####

def find_all_books(url, page):
    """find all books from an url, this functions will find books from next pages if they exist

    Args:
        url (string): URL of website we want to scrap
        page (requests.models.Response): Status code for a HTTP request from server

    Returns:
        links (list): list of all url find in all pages of the category
    """
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
        next_page_content = check_next_page(page)
        url = urljoin(url, next_page_content)
    print("Nombre de livre(s) trouvé(s) dans la catégorie : " + str(len(links)))
    return links

def main(url):
    categories = []
    links = [] 
    all_books_informations = []
    list_of_all_books_informations = []
    page = requests.get(url)
    categories = find_all_categories(url, page)
    i = 0
    for category in categories:
        links = find_all_books(category, page)
        for link in links:
            informations_livre, category = scrap_my_book(link)
            all_books_informations.append(informations_livre)
            list_of_all_books_informations.append(all_books_informations)
            # all_links.append(links)
            entetes = ["product_page_url", "universal_product_code (upc)" , "title", "price_including_tax", "price_excluding_tax", "number_available", "product_description", "category", "review_rating", "image_url"]
        write_in_csv(entetes, category, list_of_all_books_informations[i])
        i = i + 1