"""
Script to verify the RPO hours calculation for Mathis
"""
import json

# Load Mathis RPO data
with open('data/rpo/mathis_rpo.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

weekly_data = data.get('weekly', {})

# Calculate total hours for each month
print("=== WEEKLY DATA ===\n")
total_all_months = 0

for month_key in ['-2', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']:
    month_data = weekly_data.get(month_key, {})
    month_total = 0

    print(f"Month {month_key}:")
    for week_key, week_data in month_data.items():
        h_marketing = week_data.get('h_marketing', '-')
        week_label = week_data.get('week_label', 'N/A')

        # Convert to number
        if h_marketing == '-':
            h_value = 0
            print(f"  Week {week_key} ({week_label}): - (ignored in sum)")
        else:
            try:
                h_value = float(h_marketing)
                month_total += h_value
                print(f"  Week {week_key} ({week_label}): {h_value}h")
            except:
                h_value = 0
                print(f"  Week {week_key} ({week_label}): invalid ({h_marketing})")

    print(f"  -> Month {month_key} total: {month_total}h\n")
    total_all_months += month_total

print(f"=== TOTAL ALL MONTHS ===")
print(f"Total PAP hours: {total_all_months}h")

# Also check only valid months (Dec 2025 - Aug 2026)
print(f"\n=== TOTAL VALID MONTHS (Dec 2025 - Aug 2026) ===")
total_valid = 0
for month_key in ['-2', '0', '1', '2', '3', '4', '5', '6', '7']:
    month_data = weekly_data.get(month_key, {})
    for week_key, week_data in month_data.items():
        h_marketing = week_data.get('h_marketing', '-')
        if h_marketing != '-':
            try:
                total_valid += float(h_marketing)
            except:
                pass

print(f"Total PAP hours (valid period): {total_valid}h")
