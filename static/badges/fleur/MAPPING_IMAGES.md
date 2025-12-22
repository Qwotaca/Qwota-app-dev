# 🔄 Mapping des images existantes vers badge_id

Tu as déjà créé des images PNG numérotées. Voici comment les renommer:

## Images COMMUN trouvées (4 fichiers)
```
28.png → À renommer en: victoire_jitqe.png
29.png → À renommer en: costumier.png
30.png → À renommer en: pagayeurs.png
31.png → À renommer en: ho_ho_ho.png
```

## Images RARE trouvées (8 fichiers)
```
32.png → À renommer en: mvp_competition.png
33.png → À renommer en: mention_semaine.png
34.png → À renommer en: thermometre_plein.png
35.png → À renommer en: retour_2.png
36.png → À renommer en: note_peintres.png
37.png → À renommer en: vikings.png
38.png → À renommer en: eleve_parfait.png
39.png → À renommer en: formations.png
```

## Images LÉGENDAIRE trouvées (10 fichiers)
```
40.png → À renommer en: champions_jitqe.png
41.png → À renommer en: entrepreneur_semaine.png
42.png → À renommer en: pool_facile.png
43.png → À renommer en: mvp_presidents.png
44.png → À renommer en: president_1.png
45.png → À renommer en: referencoeurs.png
46.png → À renommer en: referenceurs.png
47.png → À renommer en: peintre_entrepreneur.png
48.png → À renommer en: retour_3.png
49.png → À renommer en: premier_classe.png
```

## Images MYTHIQUE trouvées (8 fichiers)
```
50.png → À renommer en: president_2.png
51.png → À renommer en: elite_1.png
52.png → À renommer en: modele_peintres.png
53.png → À renommer en: retour_4.png
54.png → À renommer en: retour_5.png
55.png → À renommer en: coach.png
56.png → À renommer en: mentor.png
57.png → (À définir - il n'y a que 7 badges mythiques dans la config)
```

## Images ÉPIQUE trouvées (4 fichiers)
```
58.png → À renommer en: president_3.png
59.png → À renommer en: elite_2.png
60.png → À renommer en: super_coach.png
61.png → À renommer en: berceuse.png
```

---

## ⚠️ IMPORTANT

L'ordre des fichiers ci-dessus est une **estimation** basée sur la numérotation.
Tu dois vérifier manuellement quelle image correspond à quel badge!

## Script de renommage (Windows)

Copie ces commandes dans un fichier `.bat` pour renommer automatiquement:

```batch
@echo off
cd /d "C:\Users\zachl\OneDrive\Bureau\qwota-app-main\static\badges\fleur"

REM COMMUN
cd commun
ren 28.png victoire_jitqe.png
ren 29.png costumier.png
ren 30.png pagayeurs.png
ren 31.png ho_ho_ho.png
cd ..

REM RARE
cd rare
ren 32.png mvp_competition.png
ren 33.png mention_semaine.png
ren 34.png thermometre_plein.png
ren 35.png retour_2.png
ren 36.png note_peintres.png
ren 37.png vikings.png
ren 38.png eleve_parfait.png
ren 39.png formations.png
cd ..

REM LÉGENDAIRE
cd legendaire
ren 40.png champions_jitqe.png
ren 41.png entrepreneur_semaine.png
ren 42.png pool_facile.png
ren 43.png mvp_presidents.png
ren 44.png president_1.png
ren 45.png referencoeurs.png
ren 46.png referenceurs.png
ren 47.png peintre_entrepreneur.png
ren 48.png retour_3.png
ren 49.png premier_classe.png
cd ..

REM MYTHIQUE
cd mythique
ren 50.png president_2.png
ren 51.png elite_1.png
ren 52.png modele_peintres.png
ren 53.png retour_4.png
ren 54.png retour_5.png
ren 55.png coach.png
ren 56.png mentor.png
cd ..

REM ÉPIQUE
cd epique
ren 58.png president_3.png
ren 59.png elite_2.png
ren 60.png super_coach.png
ren 61.png berceuse.png
cd ..

echo Renommage terminé!
pause
```

## ⚠️ Avant d'exécuter le script

1. **Vérifier manuellement** que chaque image correspond au bon badge
2. **Faire une sauvegarde** des images originales
3. Adapter le script si nécessaire selon tes besoins

## Images manquantes

Il manque encore les images pour les **Anti-Badges**:
- `evenement_manque.png` (dans anti-badge/)
- `compta_pas_facultatif.png` (dans anti-badge/)
