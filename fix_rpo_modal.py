#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour simplifier le modal RPO en utilisant allWeeksData existant
"""

with open('QE/Frontend/Coach/coach_rpo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver et remplacer la section de génération de semaines
old_section = """  console.log('[RPO MODAL] Available month indices in weekly:', Object.keys(weekly));
  console.log('[RPO MODAL] Looking for month index:', monthIndex);

  const monthData = weekly[String(monthIndex)] || {};
  const weeks = Object.keys(monthData).sort((a, b) => parseInt(a) - parseInt(b));

  console.log('[RPO MODAL] Found weeks:', weeks);
  console.log('[RPO MODAL] Month data:', monthData);

  // Générer les vraies dates de semaines pour ce mois
  function getWeeksForMonth(year, month) {
    const weeksData = [];
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);

    // Trouver le lundi de la première semaine
    let currentDate = new Date(firstDay);
    const dayOfWeek = currentDate.getDay();
    const daysToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    currentDate.setDate(currentDate.getDate() + daysToMonday);

    let weekNum = 1;
    while (currentDate <= lastDay || weekNum <= 5) {
      const weekStart = new Date(currentDate);
      const weekEnd = new Date(currentDate);
      weekEnd.setDate(weekEnd.getDate() + 6);

      const startDay = weekStart.getDate();
      const startMonth = weekStart.getMonth() + 1;
      const endDay = weekEnd.getDate();
      const endMonth = weekEnd.getMonth() + 1;

      const startMonthName = monthNames[String(startMonth).padStart(2, '0')];
      const endMonthName = monthNames[String(endMonth).padStart(2, '0')];

      let weekLabel;
      if (startMonth === endMonth) {
        weekLabel = `${startDay} - ${endDay} ${startMonthName}`;
      } else {
        weekLabel = `${startDay} ${startMonthName} - ${endDay} ${endMonthName}`;
      }

      weeksData.push({
        num: weekNum,
        label: weekLabel,
        startDate: new Date(weekStart),
        endDate: new Date(weekEnd)
      });

      currentDate.setDate(currentDate.getDate() + 7);
      weekNum++;

      if (weekNum > 5 || currentDate > new Date(lastDay.getTime() + 7 * 24 * 60 * 60 * 1000)) {
        break;
      }
    }

    return weeksData;
  }

  const weeksInfo = getWeeksForMonth(year, targetMonth);"""

new_section = """  console.log('[RPO MODAL] Available month indices in weekly:', Object.keys(weekly));
  console.log('[RPO MODAL] Looking for month index:', monthIndex);

  const monthData = weekly[String(monthIndex)] || {};
  const weeks = Object.keys(monthData).sort((a, b) => parseInt(a) - parseInt(b));

  console.log('[RPO MODAL] Found weeks:', weeks);
  console.log('[RPO MODAL] Month data:', monthData);

  // Filtrer allWeeksData pour obtenir les semaines du mois sélectionné
  const weeksForMonth = allWeeksData.filter(week => {
    // Extraire le mois de la semaine depuis le label
    const parts = week.label.split(' - ');
    if (parts.length < 2) return false;

    // Prendre la date de début de la semaine
    const startPart = parts[0].trim();
    const monthMatch = startPart.match(/(\d+)\s+(\w+)/);
    if (!monthMatch) return false;

    const monthName = monthMatch[2].toLowerCase();
    const monthNamesMap = {
      'janvier': '01', 'janv.': '01', 'février': '02', 'févr.': '02', 'mars': '03',
      'avril': '04', 'avr.': '04', 'mai': '05', 'juin': '06',
      'juillet': '07', 'juil.': '07', 'août': '08', 'septembre': '09', 'sept.': '09',
      'octobre': '10', 'oct.': '10', 'novembre': '11', 'nov.': '11', 'décembre': '12', 'déc.': '12'
    };

    return monthNamesMap[monthName] === selectedMonth;
  });

  console.log('[RPO MODAL] Weeks for month from allWeeksData:', weeksForMonth);"""

if old_section in content:
    content = content.replace(old_section, new_section)
    print("[OK] Section de génération de semaines remplacée")
else:
    print("[ERREUR] Section non trouvée")
    print("Recherche de la ligne console.log...")
    if "console.log('[RPO MODAL] Available month indices in weekly:'," in content:
        print("  -> Trouvé le début")
    if "const weeksInfo = getWeeksForMonth(year, targetMonth);" in content:
        print("  -> Trouvé la fin")

# Sauvegarder
with open('QE/Frontend/Coach/coach_rpo.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Terminé!")
