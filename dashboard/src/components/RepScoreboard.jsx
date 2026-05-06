function RepBadge({ rep, isAllied }) {
  let bgColor, borderColor, label, icon;
  
  if (rep.status === 'excluded') {
    bgColor = 'rgba(244, 63, 94, 0.1)';
    borderColor = '#f43f5e';
    label = 'Excluded';
    icon = '🚫';
  } else if (rep.status === 'supporter' && isAllied) {
    bgColor = 'rgba(139, 92, 246, 0.15)';
    borderColor = '#8b5cf6';
    label = 'Supporter + Allied';
    icon = '🤝';
  } else if (rep.status === 'supporter') {
    bgColor = 'rgba(16, 185, 129, 0.15)';
    borderColor = '#10b981';
    label = 'Supporter';
    icon = '✅';
  } else if (isAllied) {
    bgColor = 'rgba(59, 130, 246, 0.15)';
    borderColor = '#3b82f6';
    label = 'Allied';
    icon = '🔗';
  } else {
    bgColor = 'rgba(71, 85, 105, 0.15)';
    borderColor = '#475569';
    label = 'Eligible';
    icon = '👤';
  }

  return (
    <div
      className="flex flex-col p-4 rounded-xl transition-all duration-300 hover:scale-[1.02]"
      style={{ background: bgColor, border: `1px solid ${borderColor}` }}
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
          style={{ background: borderColor, color: '#0a0e1a' }}
        >
          {rep.id.replace('rep_', 'R')}
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-bold text-[var(--color-text-primary)] truncate">{rep.name || rep.id}</span>
          <span className="text-xs truncate" style={{ color: borderColor }}>{icon} {label}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2 mt-2 pt-3 border-t border-[rgba(255,255,255,0.05)]">
        <div className="flex flex-col">
          <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">Influence</span>
          <span className="text-xs font-medium text-[var(--color-text-primary)]">{rep.influence}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">Faction</span>
          <span className="text-xs font-medium text-[var(--color-text-primary)] truncate">{rep.faction}</span>
        </div>
      </div>

      {rep.reason && (
        <div className="mt-3 text-[11px] px-2 py-1.5 rounded bg-[rgba(0,0,0,0.2)] text-[var(--color-text-secondary)]">
          {rep.reason}
        </div>
      )}
    </div>
  );
}

export default function RepScoreboard({ representatives, alliances }) {
  if (!representatives) return null;

  const alliedSet = new Set();
  if (alliances) {
    alliances.forEach(a => { alliedSet.add(a.pair[0]); alliedSet.add(a.pair[1]); });
  }

  // Sort reps: Supporters first, then allied, then eligible, then excluded
  const sortedReps = [...representatives].sort((a, b) => {
    const rankA = a.status === 'supporter' ? 0 : a.status === 'excluded' ? 3 : alliedSet.has(a.id) ? 1 : 2;
    const rankB = b.status === 'supporter' ? 0 : b.status === 'excluded' ? 3 : alliedSet.has(b.id) ? 1 : 2;
    if (rankA !== rankB) return rankA - rankB;
    return b.influence - a.influence;
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {sortedReps.map(rep => (
        <RepBadge
          key={rep.id}
          rep={rep}
          isAllied={alliedSet.has(rep.id)}
        />
      ))}
    </div>
  );
}
