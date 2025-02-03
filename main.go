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
		}
	})
}
