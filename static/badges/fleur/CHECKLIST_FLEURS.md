# Checklist des Badges FLEUR 🌸

Total: 39 badges à créer

## COMMUN (25 XP) - 4 badges
Placer dans: `static/badges/fleur/commun/`

- [ ] `victoire_jitqe.png` - VICTOIRE !
- [ ] `costumier.png` - Costumier
- [ ] `pagayeurs.png` - PAGAYEURS
- [ ] `ho_ho_ho.png` - Ho ho ho !

---

## RARE (50 XP) - 8 badges
Placer dans: `static/badges/fleur/rare/`

- [ ] `mvp_competition.png` - MVP
- [ ] `mention_semaine.png` - Mention de la semaine
- [ ] `thermometre_plein.png` - Le thermomètre est plein
- [ ] `retour_2.png` - RETOUR
- [ ] `note_peintres.png` - Note des peintres
- [ ] `vikings.png` - VIKINGS
- [ ] `eleve_parfait.png` - Un élève parfait
- [ ] `formations.png` - 'Formations'

---

## ÉPIQUE (100 XP) - 4 badges
Placer dans: `static/badges/fleur/epique/`

- [ ] `president_3.png` - Président pour Toujours
- [ ] `elite_2.png` - L'élite de l'élite
- [ ] `super_coach.png` - Super Coach
- [ ] `berceuse.png` - Berceuse

---

## LÉGENDAIRE (200 XP) - 11 badges
Placer dans: `static/badges/fleur/legendaire/`

- [ ] `champions_jitqe.png` - CHAMPIONS !
- [ ] `entrepreneur_semaine.png` - Entrepreneur de la semaine
- [ ] `pool_facile.png` - Mon pool était trop facile
- [ ] `mvp_presidents.png` - MVP des Présidents
- [ ] `president_1.png` - Tu es un Président
- [ ] `referencoeurs.png` - Référen-coeurs
- [ ] `referenceurs.png` - Tu es un Référenceur
- [ ] `peintre_entrepreneur.png` - De Peintres à Entrepreneur
- [ ] `retour_3.png` - QE sur le Coeur
- [ ] `premier_classe.png` - Premier de classe

---

## MYTHIQUE (500 XP) - 10 badges
Placer dans: `static/badges/fleur/mythique/`

- [ ] `president_2.png` - Encore Président
- [ ] `elite_1.png` - Tu es Élite
- [ ] `modele_peintres.png` - Modèle pour les peintres
- [ ] `retour_4.png` - ad vitam æternam
- [ ] `retour_5.png` - QE pour la vie
- [ ] `coach.png` - Coach !!
- [ ] `mentor.png` - Mentor!!

---

## ANTI-BADGE (Pénalité) - 2 badges
Placer dans: `static/badges/fleur/anti-badge/`
⚠️ ATTENTION: Créer le dossier `anti-badge` si nécessaire

- [ ] `evenement_manque.png` - Événement Manqué
- [ ] `compta_pas_facultatif.png` - La Compta, c'est pas facultatif

---

## Format des images
- **Taille:** 512x512 pixels
- **Format:** PNG avec transparence
- **Nom:** Exactement le `badge_id` avec extension `.png`

## Test
Pour tester si l'image s'affiche:
```
http://localhost:8080/static/badges/fleur/{rareté}/{badge_id}.png
```

Exemple:
```
http://localhost:8080/static/badges/fleur/commun/victoire_jitqe.png
```
