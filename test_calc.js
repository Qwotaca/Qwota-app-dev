const weeklyData = {
  '0': {
    '1': { h_marketing: 20 },
    '2': { h_marketing: 40 },
    '3': { h_marketing: '-' }
  }
};

let totalHMarketing = 0;
const monthWeeklyData = weeklyData['0'];

Object.keys(monthWeeklyData).forEach(weekNumber => {
  const weekData = monthWeeklyData[weekNumber];

  // Ignorer les valeurs '-' mais compter les 0
  if (weekData.h_marketing !== '-' && weekData.h_marketing !== undefined) {
    totalHMarketing += parseFloat(weekData.h_marketing) || 0;
  }
});

console.log('Total h_marketing:', totalHMarketing);
