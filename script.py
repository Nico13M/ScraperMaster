import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

url = "https://monmaster.gouv.fr/formation?rechercheBrut=master%20psychologie%20clinique"

def scrape_formation(driver, url, writer):
    driver.get(url)
    time.sleep(5)

    try:
        title = driver.find_element(By.CSS_SELECTOR, "h2").text
    except:
        title = ""

    try:
        capacity = driver.find_element(By.XPATH, "//span[contains(text(), 'CAPACITÉ D’ACCUEIL')]//ancestor::p[1]//following-sibling::p").text
    except:
        capacity = ""

    try:
        key_figures = ""
        span = driver.find_element(By.XPATH, "//span[contains(text(), 'Chiffres Clés')]")
        parent_p = span.find_element(By.XPATH, "./ancestor::p[1]")
        next_ps = parent_p.find_elements(By.XPATH, "./following-sibling::p[position() <= 3]")
        
        for p in next_ps:
            lines = p.text.splitlines()
            filtered_lines = [line.strip() for line in lines if "Information contextuelle" not in line and line.strip() != ""]
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
            expected_criteria += li.text.strip() + "\n"
    except Exception as e:
        print("Erreur lors de l'extraction des critères attendus :", e)
        expected_criteria = ""

    address = ""
    try:
        address_p = driver.find_element(By.XPATH, "//p[contains(text(), 'Adresse')]")
        next_p = address_p.find_element(By.XPATH, "following-sibling::p")
        span_elements = next_p.find_elements(By.TAG_NAME, "span")
        address = " ".join([span.text for span in span_elements])
    except:
        address = ""

    writer.writerow([title, url, capacity, key_figures, expected_criteria, address, ""])

with open("formations.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Titre", "Lien", "Capacité d'accueil", "Chiffres clés", "Attendus", "Adresse", "Nombre de formations"])

    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/formation/']"))
    )

    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/formation/']")
    formation_links = [link.get_attribute('href') for link in links]

    for link in formation_links:
        print(f"Récupération de la formation: {link}")
        scrape_formation(driver, link, writer)

    driver.quit()

    print("Extraction terminée.")
