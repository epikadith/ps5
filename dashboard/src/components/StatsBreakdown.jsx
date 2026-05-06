export default function StatsBreakdown({ pipeline }) {
  if (!pipeline) return null;

  const { raw_stats, clean_stats } = pipeline;

  const steps = [
    {
      title: 'Raw Data Loaded',
      stats: [
        { label: 'Reps', val: raw_stats.representatives_loaded },
        { label: 'Proposals', val: raw_stats.proposals_loaded },
        { label: 'Relations', val: raw_stats.relations_loaded },
      ],
      color: '#3b82f6'
    },
    {
      title: 'Data Cleaning',
      stats: [
        { label: 'Reps Removed', val: clean_stats.reps_removed, isBad: true },
        { label: 'Proposals Removed', val: clean_stats.proposals_removed, isBad: true },
        { label: 'Relations Removed', val: clean_stats.relations_removed, isBad: true },
      ],
      color: '#f59e0b'
    },
    {
      title: 'Clean Data Available',
      stats: [
        { label: 'Valid Reps', val: clean_stats.representatives_after },
        { label: 'Valid Proposals', val: clean_stats.proposals_after },
        { label: 'Valid Relations', val: clean_stats.relations_after },
      ],
      color: '#10b981'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="relative border-l-2 border-[var(--color-border)] ml-3 pl-6 space-y-8">
        {steps.map((step, i) => (
          <div key={i} className="relative">
            {/* Timeline dot */}
            <div 
              className="absolute -left-[31px] top-1 w-4 h-4 rounded-full border-4 border-[var(--color-bg-card)]"
              style={{ background: step.color }}
            />
            <h4 className="text-sm font-bold text-[var(--color-text-primary)] mb-3">{step.title}</h4>
            <div className="grid grid-cols-3 gap-2">
              {step.stats.map((stat, j) => (
                <div key={j} className="bg-[rgba(255,255,255,0.03)] rounded-lg p-3 border border-[rgba(255,255,255,0.05)] flex flex-col items-center text-center">
                  <span className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">{stat.label}</span>
                  <span 
                    className="text-lg font-bold"
                    style={{ color: stat.val > 0 && stat.isBad ? '#f43f5e' : '#f1f5f9' }}
                  >
                    {stat.val > 0 && stat.isBad ? `-${stat.val}` : stat.val}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
