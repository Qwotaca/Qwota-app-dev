# Checklist des Badges ÉTOILE ⭐

Total: 34 badges à créer (Formations & Certifications)

## COMMUN (25 XP) - 8 badges
Placer dans: `static/badges/etoile/commun/`

- [ ] `maitre_estimateur.png` - Maître estimateur
- [ ] `droit_passage.png` - Droit de passage
- [ ] `producteur.png` - Producteur
- [ ] `paneliste_debutant.png` - Panéliste Débutant
- [ ] `droit_peinture.png` - Droit de peinture
- [ ] `annee_2_parti.png` - Année 2, c'est parti !!
- [ ] `pret_an_2.png` - Prêt pour l'an 2!
- [ ] `valet_formateur.png` - Valet Formateur

---

## RARE (50 XP) - 5 badges
Placer dans: `static/badges/etoile/rare/`

- [ ] `super_producteur.png` - Super Producteur
- [ ] `paneliste_agguerri.png` - Panéliste Agguerri
- [ ] `grosse_annee.png` - En route pour une grosse année
- [ ] `grafiti.png` - Grafiti !!
- [ ] `dame_formateur.png` - Dame Formateur

---

## ÉPIQUE (100 XP) - 3 badges
Placer dans: `static/badges/etoile/epique/`

- [ ] `recrutement_niveau_3.png` - Recrutement Niveau 3
- [ ] `former_releve_2.png` - Former la Relève Niveau 2
- [ ] `conferencier_expert_3.png` - Conférenciers Expert Niveau 3

---

## LÉGENDAIRE (200 XP) - 9 badges
Placer dans: `static/badges/etoile/legendaire/`

- [ ] `maitre_producteur.png` - Maître Producteur
- [ ] `paneliste_expert.png` - Panéliste Expert
- [ ] `annee_record.png` - En route pour une année record
- [ ] `roi_formateur.png` - Roi Formateur
- [ ] `recrutement_expert_1.png` - Recrutement Expert Niveau 1
- [ ] `coaching_expert_1.png` - Coaching Expert Niveau 1
- [ ] `conferencier_expert_1.png` - Conférenciers Expert Niveau 1
- [ ] `coach_terrain_expert_1.png` - Coach de terrain Expert Niveau 1
- [ ] `formateur_prod_expert_1.png` - Formateur en Production Expert Niveau 1

---

## MYTHIQUE (500 XP) - 9 badges
Placer dans: `static/badges/etoile/mythique/`

- [ ] `roi_production.png` - Le Roi de la Production
- [ ] `roi_panel.png` - Le Roi du Panel
- [ ] `meilleur_panel_senior.png` - Meilleur Panel Sénior !!
- [ ] `recrutement_expert_2.png` - Recrutement Expert Niveau 2
- [ ] `organisateur_expert_1.png` - Organisateur Expert Niveau 1
- [ ] `coaching_expert_2.png` - Coaching Expert Niveau 2
- [ ] `conferencier_expert_2.png` - Conférenciers Expert Niveau 2
- [ ] `formateur_prod_expert_2.png` - Formateur en Production Expert Niveau 2
- [ ] `former_releve_1.png` - Former la Relève Niveau 1

---

## Format des images
- **Taille:** 512x512 pixels
- **Format:** PNG avec transparence
- **Nom:** Exactement le `badge_id` avec extension `.png`
- **Style:** Étoiles représentent des accomplissements de formation/certification

## Test
Pour tester si l'image s'affiche:
```
http://localhost:8080/static/badges/etoile/{rareté}/{badge_id}.png
```

Exemple:
```
http://localhost:8080/static/badges/etoile/commun/maitre_estimateur.png
```
