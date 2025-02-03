package main 
import (
	"encoding/csv"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/PuerkitoBio/goquery"
)

const url = "https://monmaster.gouv.fr/formation?rechercheBrut=master%20psychologie%20clinique"

func main() {
	file, err := os.Create("formations.csv")
	if err != nil {
		log.Fatalf("Erreur lors de la création du fichier CSV : %v", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	writer.Write([]string{"Titre", "Lien", "Capacité d'accueil", "Chiffres clés", "Attendus", "Adresse", "Nombre de formations"})

	count := 0

	resp, err := http.Get(url)
	if err != nil {
		log.Fatalf("Erreur lors de la requête : %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Fatalf("Erreur HTTP: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		log.Fatalf("Erreur lors du parsing HTML : %v", err)
	}

	// Debug: Afficher tous les liens présents sur la page
	doc.Find("a").Each(func(index int, item *goquery.Selection) {
		link, exists := item.Attr("href")
		if exists {
			fmt.Printf("Lien %d: %s\n", index+1, link)
		}
	})

	// Rechercher les formations spécifiquement
	doc.Find("a[href*='/formation/']").Each(func(index int, item *goquery.Selection) {
		title := item.Text()
		link, exists := item.Attr("href")
		if exists {
			fullLink := "https://monmaster.gouv.fr" + link
			fmt.Printf("%d: %s - %s\n", index+1, title, fullLink)
			scrapeFormation(fullLink, writer, &count)
		}
	})

	writer.Write([]string{"", "", "", "", "", "", fmt.Sprintf("%d", count)})
	writer.Flush()

	fmt.Printf("Nombre total de formations récupérées : %d\n", count)
}

func scrapeFormation(url string, writer *csv.Writer, count *int) {
	resp, err := http.Get(url)
	if err != nil {
		log.Printf("Erreur lors de la requête de la formation %s : %v", url, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Erreur HTTP pour %s: %d", url, resp.StatusCode)
		return
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		log.Printf("Erreur lors du parsing HTML de %s : %v", url, err)
		return
	}

	title := doc.Find("h2").First().Text()
	capacity := doc.Find("span:contains('CAPACITÉ D’ACCUEIL')").Parent().Next().Text()
	keyFigures := doc.Find("p.fr-icon-line-chart-line").Text()
	doc.Find("p.fr-icon-line-chart-line").NextAllFiltered("p").Each(func(i int, s *goquery.Selection) {
		keyFigures += "\n" + s.Text()
	})

	expectedCriteria := ""
	doc.Find("app-bullet-list li").Each(func(i int, s *goquery.Selection) {
		expectedCriteria += "- " + s.Text() + "\n"
	})

	address := doc.Find("p:contains('Adresse')").Next().Text()

	writer.Write([]string{title, url, capacity, keyFigures, expectedCriteria, address, ""})
	writer.Flush()

	*count++
}
