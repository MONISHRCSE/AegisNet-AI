import React, { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import * as d3 from 'd3'
import { correlationApi } from '@/api/services'

interface Node extends d3.SimulationNodeDatum { id: string; ip: string; criticality: number; is_honeypot: boolean, type?: string, severity?: string }
interface Link { source: string; target: string; malicious: boolean, type?: string }

export default function Topology() {
  const svgRef = useRef<SVGSVGElement>(null)
  
  const { data: topologyData } = useQuery({
    queryKey: ['topologyLive'],
    queryFn: () => correlationApi.getTopologyLive(),
    refetchInterval: 10_000
  })

  useEffect(() => {
    const graph = topologyData?.data?.data || { nodes: [], edges: [] }
    if (!svgRef.current || graph.nodes.length === 0) return

    const el  = svgRef.current
    const W   = el.clientWidth  || 900
    const H   = el.clientHeight || 600

    d3.select(el).selectAll('*').remove()

    const svg = d3.select(el)
      .attr('viewBox', `0 0 ${W} ${H}`)
      .style('background', 'transparent')

    // Defs — arrow markers
    const defs = svg.append('defs')
    const mkMarker = (id: string, color: string) => {
      defs.append('marker').attr('id', id).attr('viewBox', '0 -5 10 10')
        .attr('refX', 20).attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto')
        .append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', color)
    }
    mkMarker('arrow-normal',   '#1e293b')
    mkMarker('arrow-malicious','#ff3b5c')

    const nodes: Node[] = graph.nodes.map((n: any) => ({
      id: n.id,
      ip: n.id,
      criticality: n.severity === 'critical' ? 2 : n.severity === 'high' ? 1.5 : 1,
      is_honeypot: n.type === 'honeypot',
      type: n.type,
      severity: n.severity
    }))
    
    const links: Link[] = graph.edges.map((e: any) => ({
      source: e.source,
      target: e.target,
      malicious: e.type === 'malicious_flow' || true,
      type: e.type
    }))

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(30))

    // Links
    const link = svg.append('g').selectAll('line')
      .data(links).join('line')
      .attr('stroke', (d: Link) => d.malicious ? '#ff3b5c' : '#1e293b')
      .attr('stroke-opacity', (d: Link) => d.malicious ? 0.7 : 0.3)
      .attr('stroke-width', (d: Link) => d.malicious ? 2 : 1)
      .attr('marker-end', (d: Link) => `url(#${d.malicious ? 'arrow-malicious' : 'arrow-normal'})`)

    // Node groups
    const node = svg.append('g').selectAll('g')
      .data(nodes).join('g')
      .call(d3.drag<any, Node>()
        .on('start', (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag',  (event, d) => { d.fx = event.x; d.fy = event.y })
        .on('end',   (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
      )

    // Node outer ring for honeypots / critical assets
    node.filter(d => d.is_honeypot).append('circle')
      .attr('r', 22).attr('fill', 'none').attr('stroke', '#f59e0b')
      .attr('stroke-width', 1.5).attr('stroke-dasharray', '4 2').attr('opacity', 0.7)

    // Main circle
    node.append('circle')
      .attr('r', 16)
      .attr('fill', d => d.is_honeypot ? '#1a1200' : d.criticality >= 1.3 ? '#1a0a0a' : '#0d1421')
      .attr('stroke', d => d.is_honeypot ? '#f59e0b' : d.criticality >= 1.3 ? '#ff3b5c' : '#00d4ff')
      .attr('stroke-width', 1.5)

    // IP label
    node.append('text')
      .attr('dy', 30).attr('text-anchor', 'middle')
      .attr('font-size', 9).attr('font-family', 'JetBrains Mono, monospace')
      .attr('fill', '#64748b')
      .text(d => d.ip)

    // Tick update
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x).attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x).attr('y2', (d: any) => d.target.y)
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    return () => { simulation.stop() }
  }, [topologyData])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Network Topology</h1>
        <div className="flex items-center gap-4 text-xs text-aegis-muted">
          <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-aegis-danger inline-block" /> Malicious Flow</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-aegis-warn inline-block" /> Honeypot</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full border border-aegis-accent inline-block" /> Asset</span>
        </div>
      </div>
      <div className="glass-card h-[600px] relative overflow-hidden">
        <svg ref={svgRef} className="w-full h-full" />
        <div className="absolute bottom-4 left-4 text-xs text-aegis-muted font-mono">
          Drag nodes to reposition · Red edges = active threats
        </div>
      </div>
    </div>
  )
}
