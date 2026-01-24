import gamification

print(f'Total badges: {len(gamification.BADGES_CONFIG)}')

types = {}
for k, v in gamification.BADGES_CONFIG.items():
    t = v['type']
    types[t] = types.get(t, 0) + 1

print('\nPar type:')
for k, v in sorted(types.items()):
    print(f'  {k}: {v}')

automatiques = sum(1 for v in gamification.BADGES_CONFIG.values() if v.get('automatic', False))
print(f'\nBadges automatisables: {automatiques}')
print(f'Badges manuels: {len(gamification.BADGES_CONFIG) - automatiques}')

# Compter par rareté
rarities = {}
for v in gamification.BADGES_CONFIG.values():
    r = v['rarity']
    rarities[r] = rarities.get(r, 0) + 1

print('\nPar rareté:')
for k, v in sorted(rarities.items()):
    print(f'  {k}: {v}')

print('\n✓ Configuration valide!')
