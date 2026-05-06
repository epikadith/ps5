import { useEffect } from 'react';
import useStore from './store';
import NetworkGraph from './components/NetworkGraph';
import ProposalChart from './components/ProposalChart';
import RepScoreboard from './components/RepScoreboard';
import StatsBreakdown from './components/StatsBreakdown';

function StatCard({ value, label, icon, color, delay = 0 }) {
  return (
    <div
      className="stat-badge fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <span className="text-2xl mb-1">{icon}</span>
      <span className="text-3xl font-extrabold" style={{ color }}>{value}</span>
      <span className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mt-1">{label}</span>
    </div>
  );
}

function SectionHeader({ title, subtitle, icon }) {
  return (
    <div className="mb-5">
      <h2 className="text-xl font-bold text-[var(--color-text-primary)] flex items-center gap-2">
        <span>{icon}</span>
        {title}
      </h2>
      {subtitle && <p className="text-sm text-[var(--color-text-muted)] mt-1">{subtitle}</p>}
    </div>
  );
}

export default function App() {
  const { analysis, agreement, loading, error, fetchData } = useStore();

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent-blue)] animate-spin mx-auto mb-4" />
          <p className="text-[var(--color-text-secondary)] text-sm">Loading full pipeline analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass-card p-8 text-center max-w-md">
          <span className="text-4xl mb-4 block">⚠️</span>
          <h2 className="text-xl font-bold text-[var(--color-accent-rose)] mb-2">Error Loading Data</h2>
          <p className="text-[var(--color-text-muted)] text-sm">{error}</p>
        </div>
      </div>
    );
  }

  // The actual final results
  const proposals = agreement?.final_agreement?.proposals || [];
  const supporters = agreement?.final_agreement?.supporting_reps || [];
  const finalAlliances = agreement?.alliances || [];

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-[1400px] mx-auto pb-20">
      {/* Header */}
      <header className="mb-8 fade-in-up">
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-accent-blue)] to-[var(--color-accent-purple)] flex items-center justify-center pulse-glow">
            <span className="text-2xl">🏛️</span>
          </div>
          <div>
            <h1 className="text-3xl font-extrabold bg-gradient-to-r from-[var(--color-accent-blue)] via-[var(--color-accent-purple)] to-[var(--color-accent-cyan)] bg-clip-text text-transparent">
              Phantom Consensus
            </h1>
            <p className="text-sm text-[var(--color-text-secondary)] mt-1">Full Strategic Pipeline Visibility</p>
          </div>
        </div>
      </header>

      {/* Main Final Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <StatCard value={proposals.length} label="Selected Proposals" icon="📜" color="#3b82f6" delay={100} />
        <StatCard value={supporters.length} label="Supporters" icon="👥" color="#10b981" delay={200} />
        <StatCard value={finalAlliances.length} label="Alliances" icon="🤝" color="#8b5cf6" delay={300} />
        <StatCard
          value={analysis?.trojan_horses?.length || 0}
          label="Trojans Detected"
          icon="🛡️"
          color="#f43f5e"
          delay={400}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Pipeline & Proposals */}
        <div className="lg:col-span-1 space-y-8">
          
          {/* Pipeline Details */}
          <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '200ms' }}>
            <SectionHeader title="Data Cleaning Pipeline" subtitle="How raw data was filtered" icon="🧹" />
            <StatsBreakdown pipeline={analysis?.pipeline} />
          </div>

          {/* Proposal Pipeline Chart */}
          <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '300ms' }}>
            <SectionHeader title="Proposal Evaluation" subtitle="All proposals scored and filtered" icon="📊" />
            <ProposalChart proposals={analysis?.proposals} />
          </div>
        </div>

        {/* Right Columns: Network & Scoreboard */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Alliance Network */}
          <div className="glass-card p-6 fade-in-up relative" style={{ animationDelay: '400ms' }}>
            <SectionHeader title="Strategic Alliance Network" subtitle="Full network of active representatives and alliances" icon="🕸️" />
            <NetworkGraph 
              representatives={analysis?.representatives} 
              alliances={analysis?.alliances} 
              relations={analysis?.relations}
            />
            <div className="flex flex-wrap gap-4 mt-6 justify-center bg-[rgba(0,0,0,0.2)] p-3 rounded-lg border border-[rgba(255,255,255,0.05)]">
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#8b5cf6]" /><span className="text-xs text-[var(--color-text-muted)]">Supporter + Allied</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#3b82f6]" /><span className="text-xs text-[var(--color-text-muted)]">Allied Only</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#10b981]" /><span className="text-xs text-[var(--color-text-muted)]">Supporter Only</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#475569]" /><span className="text-xs text-[var(--color-text-muted)]">Eligible</span></div>
            </div>
          </div>

          {/* Full Rep Scoreboard */}
          <div className="glass-card p-6 fade-in-up" style={{ animationDelay: '500ms' }}>
            <SectionHeader title="Representative Scoreboard" subtitle="Detailed breakdown of every representative's strategic status" icon="🎖️" />
            <RepScoreboard 
              representatives={analysis?.representatives} 
              alliances={analysis?.alliances} 
            />
          </div>
        </div>
      </div>
    </div>
  );
}
