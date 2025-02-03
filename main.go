package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/PuerkitoBio/goquery"
)

const url = "https://monmaster.gouv.fr/formation?rechercheBrut=master%20psychologie%20clinique"

func main() {
	// Faire la requête HTTP
	resp, err := http.Get(url)
	if err != nil {
		log.Fatalf("Erreur lors de la requête : %v", err)
	}
	defer resp.Body.Close()

	// Vérifier le statut de la réponse
	if resp.StatusCode != http.StatusOK {
		log.Fatalf("Erreur HTTP: %d", resp.StatusCode)
	}

	// Parser la page avec goquery
	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		log.Fatalf("Erreur lors du parsing HTML : %v", err)
	}

	// Sélectionner les formations et extraire les titres et liens
	doc.Find("a[href*='/formation/']").Each(func(index int, item *goquery.Selection) {
		title := item.Text()
		link, exists := item.Attr("href")
		if exists {
			fmt.Printf("%d: %s - %s\n", index+1, title, "https://monmaster.gouv.fr"+link)
			scrapeFormation("https://monmaster.gouv.fr" + link)
		}
	})
}

func scrapeFormation(url string) {
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

	fmt.Printf("\nFormation: %s\nCapacité d'accueil: %s\nChiffres clés:\n%s\nAttendus:\n%s\n", title, capacity, keyFigures, expectedCriteria)
}
