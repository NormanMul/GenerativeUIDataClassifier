import { useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";

export interface LineageNode {
  id: string;
  label: string;
  type?: string;
}

export interface LineageEdge {
  source: string;
  target: string;
  label?: string;
}

interface LineageGraphProps {
  data: {
    nodes: LineageNode[];
    edges: LineageEdge[];
  };
  onNodeSelect?: (node: LineageNode) => void;
  width?: number;
  height?: number;
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type?: string;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  label?: string;
}

const NODE_COLORS: Record<string, string> = {
  table: "#3b82f6",
  transformation: "#f97316",
  source: "#22c55e",
  view: "#8b5cf6",
  default: "#6b7280",
};

function nodeColor(type?: string): string {
  return NODE_COLORS[type ?? ""] ?? NODE_COLORS.default;
}

export default function LineageGraph({
  data,
  onNodeSelect,
  width = 700,
  height = 400,
}: LineageGraphProps): React.JSX.Element {
  const svgRef = useRef<SVGSVGElement>(null);
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null);

  const render = useCallback(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    if (data.nodes.length === 0) return;

    const nodes: SimNode[] = data.nodes.map((n) => ({ ...n }));
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const links: SimLink[] = data.edges
      .filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e) => ({ source: e.source, target: e.target, label: e.label }));

    // Zoom container
    const g = svg.append("g");
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr("transform", event.transform.toString());
      });
    svg.call(zoom);

    // Arrow marker
    svg
      .append("defs")
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 22)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#94a3b8");

    // Simulation
    const simulation = d3
      .forceSimulation<SimNode>(nodes)
      .force(
        "link",
        d3.forceLink<SimNode, SimLink>(links).id((d) => d.id).distance(120),
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(30));
    simRef.current = simulation;

    // Links
    const link = g
      .selectAll<SVGLineElement, SimLink>("line")
      .data(links)
      .join("line")
      .attr("stroke", "#94a3b8")
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#arrowhead)");

    // Edge labels (visible on hover of link)
    const edgeLabel = g
      .selectAll<SVGTextElement, SimLink>("text.edge-label")
      .data(links.filter((l) => l.label))
      .join("text")
      .attr("class", "edge-label")
      .attr("text-anchor", "middle")
      .attr("fill", "#64748b")
      .attr("font-size", 10)
      .attr("opacity", 0)
      .text((d) => d.label ?? "");

    link
      .on("mouseenter", (_, d) => {
        edgeLabel.filter((l) => l === d).attr("opacity", 1);
      })
      .on("mouseleave", () => {
        edgeLabel.attr("opacity", 0);
      });

    // Node groups
    const node = g
      .selectAll<SVGGElement, SimNode>("g.node")
      .data(nodes)
      .join("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    node
      .append("circle")
      .attr("r", 14)
      .attr("fill", (d) => nodeColor(d.type))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    node
      .append("text")
      .attr("dy", 28)
      .attr("text-anchor", "middle")
      .attr("fill", "#334155")
      .attr("font-size", 11)
      .attr("font-weight", 500)
      .text((d) => d.label);

    node.on("click", (_, d) => {
      onNodeSelect?.({ id: d.id, label: d.label, type: d.type });
    });

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x!)
        .attr("y1", (d) => (d.source as SimNode).y!)
        .attr("x2", (d) => (d.target as SimNode).x!)
        .attr("y2", (d) => (d.target as SimNode).y!);

      edgeLabel
        .attr("x", (d) => ((d.source as SimNode).x! + (d.target as SimNode).x!) / 2)
        .attr("y", (d) => ((d.source as SimNode).y! + (d.target as SimNode).y!) / 2 - 6);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });
  }, [data, width, height, onNodeSelect]);

  useEffect(() => {
    render();
    return () => {
      simRef.current?.stop();
    };
  }, [render]);

  if (data.nodes.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded border border-dashed border-gray-300 bg-gray-50 text-sm text-gray-400">
        No lineage data available
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded border border-gray-200 bg-white">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="w-full"
        viewBox={`0 0 ${width} ${height}`}
      />
      <div className="flex gap-4 border-t border-gray-100 px-3 py-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-blue-500" /> Table
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-orange-500" /> Transformation
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500" /> Source
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-purple-500" /> View
        </span>
      </div>
    </div>
  );
}
