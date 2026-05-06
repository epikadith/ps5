import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function NetworkGraph({ representatives, alliances, relations }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || !representatives) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = 400;

    // Build nodes from all eligible/supporter reps
    const nodes = representatives
      .filter(r => r.status !== 'excluded')
      .map(r => ({
        id: r.id,
        name: r.name,
        faction: r.faction,
        isSupporter: r.status === 'supporter',
        isAllied: alliances.some(a => a.pair.includes(r.id)),
      }));

    if (nodes.length === 0) {
      d3.select(svgRef.current).selectAll('*').remove();
      d3.select(svgRef.current)
        .append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#64748b')
        .text('No active representatives to display');
      return;
    }

    // Build links only between active nodes
    const activeIds = new Set(nodes.map(n => n.id));
    const links = alliances
      .filter(a => activeIds.has(a.pair[0]) && activeIds.has(a.pair[1]))
      .map(a => ({ source: a.pair[0], target: a.pair[1] }));

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Gradient defs
    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient')
      .attr('id', 'linkGradient')
      .attr('gradientUnits', 'userSpaceOnUse');
    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#3b82f6');
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#8b5cf6');

    // Glow filter
    const filter = defs.append('filter').attr('id', 'glow');
    filter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'blur');
    filter.append('feMerge')
      .selectAll('feMergeNode')
      .data(['blur', 'SourceGraphic'])
      .enter().append('feMergeNode')
      .attr('in', d => d);

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Tooltip
    const tooltip = d3.select(containerRef.current)
      .append('div')
      .attr('class', 'tooltip-d3')
      .style('opacity', 0);

    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', 'url(#linkGradient)')
      .attr('stroke-width', 3)
      .attr('stroke-opacity', 0.7)
      .attr('class', 'network-link');

    const nodeGroup = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'network-node')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x; d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null; d.fy = null;
        })
      )
      .on('mouseover', (event, d) => {
        tooltip.transition().duration(200).style('opacity', 1);
        tooltip.html(`
          <div class="font-bold text-white">${d.name}</div>
          <div class="text-xs text-gray-400">${d.id} | ${d.faction}</div>
          <div class="mt-1 text-xs px-2 py-1 rounded inline-block ${
            d.isAllied && d.isSupporter ? 'bg-purple-900/50 text-purple-300' :
            d.isAllied ? 'bg-blue-900/50 text-blue-300' :
            d.isSupporter ? 'bg-emerald-900/50 text-emerald-300' : 'bg-slate-800 text-slate-300'
          }">
            ${d.isAllied && d.isSupporter ? 'Supporter + Allied' :
              d.isAllied ? 'Allied' :
              d.isSupporter ? 'Supporter' : 'Eligible'}
          </div>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', () => {
        tooltip.transition().duration(500).style('opacity', 0);
      });

    // Outer glow ring for allied nodes
    nodeGroup.filter(d => d.isAllied)
      .append('circle')
      .attr('r', 28)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.4)
      .attr('filter', 'url(#glow)');

    // Main node circle
    nodeGroup.append('circle')
      .attr('r', 22)
      .attr('fill', d => {
        if (d.isAllied && d.isSupporter) return '#8b5cf6';
        if (d.isAllied) return '#3b82f6';
        if (d.isSupporter) return '#10b981';
        return '#475569';
      })
      .attr('stroke', '#1e293b')
      .attr('stroke-width', 2);

    // Node labels
    nodeGroup.append('text')
      .text(d => d.id.replace('rep_', 'R'))
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .style('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
      d3.select(containerRef.current).selectAll('.tooltip-d3').remove();
    };
  }, [representatives, alliances, relations]);

  return (
    <div ref={containerRef} className="w-full relative">
      <svg ref={svgRef} className="w-full" />
    </div>
  );
}
