import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# URL de base avec le paramètre page
base_url = "https://monmaster.gouv.fr/formation?rechercheBrut=master%20psychologie%20clinique&page="

def clean_text(text):
    """ Nettoie le texte en supprimant les retours à la ligne et espaces inutiles """
    return text.replace("\n", " ").replace("\r", " ").strip()

def scrape_pieces_demandees(driver, formation_url):
    """ Récupère les pièces demandées depuis la page spécifique """
    pieces_url = formation_url + "/piecesdemandees"
    driver.get(pieces_url)
    time.sleep(3)

    pieces_data = []
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h2")))
        h2_elements = driver.find_elements(By.TAG_NAME, "h2")
        
        for h2 in h2_elements:
            titre_piece = clean_text(h2.text)
            div_sibling = h2.find_element(By.XPATH, "following-sibling::div[1]")
            try:
                span_element = div_sibling.find_element(By.TAG_NAME, "span")
                hint_text_span = span_element.find_element(By.CLASS_NAME, "fr-hint-text")
                contenu_piece = clean_text(hint_text_span.text)
            except:
                contenu_piece = ""

            # Vérification avant d'ajouter à la liste
            if "Panneau de gestion des cookies" not in titre_piece:
                pieces_data.append(f"{titre_piece}: {contenu_piece}")
    except Exception as e:
        print(f"Erreur lors de l'extraction des pièces demandées pour {formation_url}: {e}")
    
    return " | ".join(pieces_data) if pieces_data else ""

def scrape_formation(driver, url, writer):
    driver.get(url)
    time.sleep(5)

    try:
        mention = clean_text(driver.find_element(By.CSS_SELECTOR, "h1").text)
    except:
        mention = ""
        
    try:
        parcours = clean_text(driver.find_element(By.CSS_SELECTOR, "h2").text)
        if "Panneau de gestion des cookies" in parcours:
            parcours = "" 
    except:
        parcours = ""

    try:
        capacity = clean_text(driver.find_element(By.XPATH, "//span[contains(text(), 'CAPACITÉ D’ACCUEIL')]//ancestor::p[1]//following-sibling::p").text)
    except:
        capacity = ""

    try:
        key_figures = ""
        span = driver.find_element(By.XPATH, "//span[contains(text(), 'Chiffres Clés')]")
        parent_p = span.find_element(By.XPATH, "./ancestor::p[1]")
        next_ps = parent_p.find_elements(By.XPATH, "./following-sibling::p[position() <= 3]")

        for p in next_ps:
            lines = p.text.splitlines()
            filtered_lines = [clean_text(line) for line in lines if "Information contextuelle" not in line and line.strip() != ""]
            if filtered_lines:
                key_figures += " ".join(filtered_lines) + ", "
    except Exception as e:
        print("Erreur lors de l'extraction des chiffres clés :", e)
        key_figures = ""

    expected_criteria = ""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//p[span[contains(text(), 'Attendus pour être admis dans cette formation')]]"))
        )

        p_element = driver.find_element(By.XPATH, "//p[span[contains(text(), 'Attendus pour être admis dans cette formation')]]")
        div_element = p_element.find_element(By.XPATH, "following-sibling::div")
        ul_element = div_element.find_element(By.XPATH, ".//ul")

        try:
            voir_plus_button = ul_element.find_element(By.XPATH, ".//button[contains(text(), 'Voir plus')]")
            voir_plus_button.click()
            WebDriverWait(driver, 5).until(
                EC.staleness_of(voir_plus_button)
            )
        except:
            pass

        li_elements = ul_element.find_elements(By.XPATH, ".//li")

        for li in li_elements:
            expected_criteria += clean_text(li.text) + " "
    except Exception as e:
        print("Erreur lors de l'extraction des critères attendus :", e)
        expected_criteria = ""

    address = ""
    try:
        address_p = driver.find_element(By.XPATH, "//p[contains(text(), 'Adresse')]")
        next_p = address_p.find_element(By.XPATH, "following-sibling::p")
        span_elements = next_p.find_elements(By.TAG_NAME, "span")
        address = clean_text(" ".join([span.text for span in span_elements]))
    except:
        address = ""

    # Récupération des pièces demandées
    pieces_demandees = scrape_pieces_demandees(driver, url)

    writer.writerow([mention, parcours, url, capacity, key_figures, expected_criteria, address, pieces_demandees])


def get_all_formations(driver, writer):
    page = 1
    while True:
        url = base_url + str(page)
        driver.get(url)
        time.sleep(5)

        print(f"Page {page}")  # Affiche la page actuelle

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/formation/']"))
            )
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/formation/']")
            formation_links = [link.get_attribute('href') for link in links]
            if not formation_links:
                break  # Si la page ne contient pas de formations, on arrête

            for link in formation_links:
                print(f"Récupération de la formation: {link}")
                scrape_formation(driver, link, writer)

            page += 1  # Passe à la page suivante
        except Exception as e:
            print("Erreur lors de la récupération des formations :", e)
            break

with open("formations.csv", mode="w", newline="", encoding="utf-8-sig") as file:
    writer = csv.writer(file, delimiter=";")  # Ajout du délimiteur ";"
    writer.writerow(["Mention","Parcours", "Lien", "Capacité d'accueil", "Chiffres clés", "Attendus", "Adresse", "Pièces demandées"])

    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Lancement du scraping pour toutes les pages
    get_all_formations(driver, writer)

    driver.quit()

print("Extraction terminée.")
