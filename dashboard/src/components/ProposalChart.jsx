import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const COLORS = {
  selected: '#10b981',
  rejected: '#f43f5e'
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="glass-card" style={{ padding: '12px 16px', fontSize: '13px', width: '220px' }}>
        <p style={{ color: '#f1f5f9', fontWeight: 600, margin: 0, borderBottom: '1px solid #1e293b', paddingBottom: '8px', marginBottom: '8px' }}>
          {data.title}
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
          <span style={{ color: '#94a3b8' }}>ID:</span>
          <span style={{ color: '#f1f5f9', textAlign: 'right' }}>{data.fullId}</span>
          
          <span style={{ color: '#94a3b8' }}>Priority:</span>
          <span style={{ color: '#f1f5f9', textAlign: 'right' }}>{data.priority}</span>
          
          <span style={{ color: '#94a3b8' }}>Viability:</span>
          <span style={{ color: '#f1f5f9', textAlign: 'right' }}>{data.viability.toFixed(2)}</span>
          
          <span style={{ color: '#94a3b8' }}>Obj Weight:</span>
          <span style={{ color: '#f1f5f9', textAlign: 'right' }}>{data.objection_weight}</span>
        </div>
        <div style={{ 
          marginTop: '10px', 
          padding: '6px', 
          borderRadius: '6px', 
          background: data.status === 'selected' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          color: data.status === 'selected' ? '#10b981' : '#f43f5e',
          fontSize: '11px',
          textAlign: 'center'
        }}>
          {data.reason}
        </div>
      </div>
    );
  }
  return null;
};

export default function ProposalChart({ proposals }) {
  if (!proposals || proposals.length === 0) return null;

  // Sort by viability descending
  const sortedProposals = [...proposals].sort((a, b) => b.viability - a.viability);

  const data = sortedProposals.map(p => ({
    name: p.id.replace('prop_', 'P'),
    fullId: p.id,
    title: p.title,
    priority: p.priority,
    viability: p.viability,
    objection_weight: p.objection_weight,
    status: p.status,
    reason: p.reason
  }));

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
          <YAxis stroke="#64748b" fontSize={12} label={{ value: 'Viability Score', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 12, offset: -5 }} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b', opacity: 0.4 }} />
          <Bar dataKey="viability" radius={[6, 6, 0, 0]} maxBarSize={50}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.status]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
