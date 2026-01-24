"""
Script to convert all static CIBLÉ (budget) td elements to editable input fields
in the États des résultats section of the RPO page
"""
import re

# Read the file
with open('QE/Frontend/Entrepreneurs/General/RPO/rpo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# List of all expense categories to update (based on data-category attributes seen)
categories = [
    ("concours", "0$", "0%"),
    ("essence", "2,500$", "1.67%"),
    ("entretien-voiture", "750$", "0.50%"),
    ("fourniture-bureau", "150$", "0.10%"),
    ("frais-bancaires", "150$", "0.10%"),
    ("frais-cellulaire", "250$", "0.17%"),
    ("frais-garanties", "4,500$", "3.00%"),
    ("leads", "200$", "0.13%"),
    ("peinture", "13,500$", "9.00%"),
    ("petits-outils", "6,000$", "4.00%"),
    ("repas", "500$", "0.33%"),
    ("redevances", "30,000$", "20.00%"),
    ("salaire-peintres", "45,000$", "30.00%"),
    ("salaires-representant", "2,000$", "1.33%"),
]

# Pattern to find and replace the CIBLÉ columns
# We need to find two consecutive td elements before the "ÉCART" section and the actuel data-field
for category, montant, percent in categories:
    # Find the pattern where actuel-montant exists with this category
    # We work backwards from the actuel field

    # Pattern: look for the specific budget amount and percentage, followed by écart columns, then actuel
    # The pattern is: two static td for CIBLÉ, two static td for ÉCART, then the actuel input

    # First, let's find and replace the montant column (CIBLÉ column 1)
    # Looking for: <td ...>MONTANT$</td>  where it's before the ÉCART columns
    pattern_montant = (
        rf'(<td style="padding: 0\.75rem 1rem; text-align: left; color: var\(--text-[^)]+\); '
        rf'border-bottom: 1px solid var\(--border-dark\); border-left: 2px solid var\(--border-dark\); '
        rf'background: rgba\(15, 23, 42, 0\.6\);">){re.escape(montant)}(</td>)'
        rf'(\s+<td style="padding: 0\.75rem 1rem; text-align: right; color: [^;]+; '
        rf'border-bottom: 1px solid var\(--border-dark\); background: rgba\(15, 23, 42, 0\.6\);">){re.escape(percent)}(</td>)'
        rf'(\s+<td style="padding: 0\.75rem 1rem; text-align: left; [^>]+>0\$</td>)'
        rf'(\s+<td style="padding: 0\.75rem 1rem; text-align: right; [^>]+>0\.00%</td>)'
        rf'(\s+<td data-field="actuel-montant" data-category="{category}")'
    )

    replacement = (
        rf'<td data-field="cible-montant" data-category="{category}" '
        rf'style="text-align: left; border-left: 2px solid var(--border-dark); border-bottom: 1px solid var(--border-dark); '
        rf'padding-left: 1rem; background: rgba(15, 23, 42, 0.6);"><input type="text" readonly '
        rf'class="etats-resultats-cible-input bg-transparent border-none w-full" '
        rf'style="color: var(--text-light); outline: none; text-align: left;" value="{montant}"></td>\3{percent}\4\5\6\7'
    )

    content = re.sub(pattern_montant, replacement, content, flags=re.DOTALL)
    print(f"Updated {category}: {montant}, {percent}")

# Write the updated content back
with open('QE/Frontend/Entrepreneurs/General/RPO/rpo.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ All CIBLÉ columns updated successfully!")
