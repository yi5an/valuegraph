"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Search, ArrowUpCircle, ArrowDownCircle, AlertTriangle, X, Network, Trophy, TrendingUp } from "lucide-react";
import { KGNode, KGEdge, KGResponse, InfluenceItem } from "@/lib/types";
import { getGraphData, getSupplyChain, getRiskPropagation, getInfluence } from "@/lib/api";

interface NodePosition {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const NODE_COLORS: Record<string, string> = {
  company: "#3b82f6",
  person: "#10b981",
  stock: "#6366f1",
  industry: "#f59e0b",
  event: "#ef4444",
};

const EDGE_COLORS: Record<string, string> = {
  invests_in: "#8b5cf6",
  supplies_to: "#06b6d4",
  competes_with: "#f43f5e",
  RELATED_TO: "#64748b",
};

function simpleForceLayout(
  nodes: KGNode[],
  edges: KGEdge[],
  width: number,
  height: number,
  iterations = 100
): Map<string, NodePosition> {
  const positions = new Map<string, NodePosition>();
  
  // Initialize positions in a circle
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;
  
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / nodes.length;
    positions.set(node.id, {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      vx: 0,
      vy: 0,
    });
  });
  
  // Build edge map
  const edgeMap = new Map<string, string[]>();
  edges.forEach((edge) => {
    if (!edgeMap.has(edge.source)) edgeMap.set(edge.source, []);
    if (!edgeMap.has(edge.target)) edgeMap.set(edge.target, []);
    edgeMap.get(edge.source)!.push(edge.target);
    edgeMap.get(edge.target)!.push(edge.source);
  });
  
  // Simple force simulation
  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion between nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const pos1 = positions.get(nodes[i].id)!;
        const pos2 = positions.get(nodes[j].id)!;
        const dx = pos2.x - pos1.x;
        const dy = pos2.y - pos1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = 5000 / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        pos1.vx -= fx;
        pos1.vy -= fy;
        pos2.vx += fx;
        pos2.vy += fy;
      }
    }
    
    // Attraction along edges
    edges.forEach((edge) => {
      const pos1 = positions.get(edge.source);
      const pos2 = positions.get(edge.target);
      if (!pos1 || !pos2) return;
      
      const dx = pos2.x - pos1.x;
      const dy = pos2.y - pos1.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - 150) * 0.05;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      pos1.vx += fx;
      pos1.vy += fy;
      pos2.vx -= fx;
      pos2.vy -= fy;
    });
    
    // Center gravity
    nodes.forEach((node) => {
      const pos = positions.get(node.id)!;
      pos.vx += (centerX - pos.x) * 0.01;
      pos.vy += (centerY - pos.y) * 0.01;
    });
    
    // Apply velocities
    nodes.forEach((node) => {
      const pos = positions.get(node.id)!;
      pos.x += pos.vx * 0.1;
      pos.y += pos.vy * 0.1;
      pos.vx *= 0.9;
      pos.vy *= 0.9;
      
      // Boundary
      pos.x = Math.max(50, Math.min(width - 50, pos.x));
      pos.y = Math.max(50, Math.min(height - 50, pos.y));
    });
  }
  
  return positions;
}

function ArrowMarker() {
  return (
    <defs>
      <marker
        id="arrowhead"
        markerWidth="10"
        markerHeight="7"
        refX="9"
        refY="3.5"
        orient="auto"
      >
        <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
      </marker>
    </defs>
  );
}

export default function GraphPage() {
  const [query, setQuery] = useState("");
  const [nodes, setNodes] = useState<KGNode[]>([]);
  const [edges, setEdges] = useState<KGEdge[]>([]);
  const [positions, setPositions] = useState<Map<string, NodePosition>>(new Map());
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [influenceData, setInfluenceData] = useState<InfluenceItem[]>([]);
  const [loadingInfluence, setLoadingInfluence] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);
  
  const width = 800;
  const height = 600;
  
  const updateLayout = useCallback(() => {
    if (nodes.length === 0) return;
    const newPositions = simpleForceLayout(nodes, edges, width, height);
    setPositions(newPositions);
  }, [nodes, edges]);
  
  useEffect(() => {
    updateLayout();
  }, [nodes, edges, updateLayout]);
  
  // Load influence data on mount
  useEffect(() => {
    const fetchInfluence = async () => {
      setLoadingInfluence(true);
      try {
        const response = await getInfluence(20);
        if (response.success && response.data) {
          setInfluenceData(response.data);
        }
      } catch (err) {
        console.error("Failed to fetch influence data:", err);
      } finally {
        setLoadingInfluence(false);
      }
    };
    fetchInfluence();
  }, []);
  
  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    
    try {
      const response = await getGraphData(query.trim());
      if (response.success && response.data) {
        setNodes(response.data.nodes);
        setEdges(response.data.edges);
      } else {
        setError("未找到相关数据");
        setNodes([]);
        setEdges([]);
      }
    } catch (err) {
      setError("查询失败，请稍后重试");
      setNodes([]);
      setEdges([]);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSupplyChain = async (direction: "upstream" | "downstream") => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getSupplyChain(query.trim(), direction);
      if (response.success && response.data) {
        setNodes(response.data.nodes);
        setEdges(response.data.edges);
      } else {
        setError("未找到产业链数据");
      }
    } catch (err) {
      setError("查询失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };
  
  const handleRiskAnalysis = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getRiskPropagation(query.trim());
      if (response.success && response.data) {
        setNodes(response.data.nodes);
        setEdges(response.data.edges);
      } else {
        setError("未找到风险传导数据");
      }
    } catch (err) {
      setError("查询失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };
  
  const handleMouseDown = (nodeId: string, e: React.MouseEvent) => {
    e.preventDefault();
    setDragging(nodeId);
  };
  
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging || !svgRef.current) return;
    
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setPositions((prev) => {
      const newPositions = new Map(prev);
      const pos = newPositions.get(dragging);
      if (pos) {
        newPositions.set(dragging, { ...pos, x, y });
      }
      return newPositions;
    });
  };
  
  const handleMouseUp = () => {
    setDragging(null);
  };
  
  const getNodeColor = (type: string) => NODE_COLORS[type] || "#64748b";
  const getEdgeColor = (type: string) => EDGE_COLORS[type] || "#64748b";
  
  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      {/* Main graph area */}
      <div className="flex-1 flex flex-col">
        {/* Search bar */}
        <div className="mb-4 flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="输入公司名称查询知识图谱..."
              className="w-full rounded-xl border border-white/10 bg-card/80 py-3 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "查询中..." : "查询"}
          </button>
        </div>
        
        {/* Graph visualization */}
        <div className="flex-1 rounded-2xl border border-white/10 bg-card/50 p-4 overflow-hidden">
          {nodes.length > 0 ? (
            <svg
              ref={svgRef}
              width="100%"
              height="100%"
              viewBox={`0 0 ${width} ${height}`}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="cursor-move"
            >
              <ArrowMarker />
              
              {/* Edges */}
              {edges.map((edge, idx) => {
                const sourcePos = positions.get(edge.source);
                const targetPos = positions.get(edge.target);
                if (!sourcePos || !targetPos) return null;
                
                const dx = targetPos.x - sourcePos.x;
                const dy = targetPos.y - sourcePos.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const nodeRadius = 20;
                const targetX = targetPos.x - (dx / dist) * nodeRadius;
                const targetY = targetPos.y - (dy / dist) * nodeRadius;
                
                return (
                  <g key={`edge-${idx}`}>
                    <line
                      x1={sourcePos.x}
                      y1={sourcePos.y}
                      x2={targetX}
                      y2={targetY}
                      stroke={getEdgeColor(edge.type)}
                      strokeWidth={2}
                      strokeOpacity={0.6}
                      markerEnd="url(#arrowhead)"
                    />
                    <text
                      x={(sourcePos.x + targetPos.x) / 2}
                      y={(sourcePos.y + targetPos.y) / 2}
                      fill="#94a3b8"
                      fontSize={10}
                      textAnchor="middle"
                      dy={-5}
                    >
                      {edge.type}
                    </text>
                  </g>
                );
              })}
              
              {/* Nodes */}
              {nodes.map((node) => {
                const pos = positions.get(node.id);
                if (!pos) return null;
                
                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onMouseDown={(e) => handleMouseDown(node.id, e)}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer"
                  >
                    <circle
                      r={20}
                      fill={getNodeColor(node.type)}
                      stroke={selectedNode?.id === node.id ? "#fff" : "transparent"}
                      strokeWidth={2}
                      className="transition-all hover:opacity-80"
                    />
                    <text
                      y={35}
                      fill="#e2e8f0"
                      fontSize={11}
                      textAnchor="middle"
                      fontWeight={500}
                    >
                      {node.name.length > 6 ? node.name.substring(0, 6) + "..." : node.name}
                    </text>
                  </g>
                );
              })}
            </svg>
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center text-slate-500">
                <Network className="mx-auto h-16 w-16 mb-4 opacity-50" />
                <p>输入公司名称开始探索知识图谱</p>
              </div>
            </div>
          )}
          
          {error && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 rounded-lg bg-red-500/20 px-4 py-2 text-sm text-red-400">
              {error}
            </div>
          )}
        </div>
      </div>
      
      {/* Side panel */}
      <div className="w-80 shrink-0 space-y-4">
        {/* Analysis buttons */}
        <div className="rounded-2xl border border-white/10 bg-card/80 p-4">
          <h3 className="mb-3 text-sm font-medium text-white">产业链分析</h3>
          <div className="space-y-2">
            <button
              onClick={() => handleSupplyChain("upstream")}
              disabled={loading || !query.trim()}
              className="flex w-full items-center gap-2 rounded-xl bg-cyan-500/20 px-4 py-2.5 text-sm text-cyan-400 hover:bg-cyan-500/30 disabled:opacity-50"
            >
              <ArrowUpCircle className="h-4 w-4" />
              上游企业
            </button>
            <button
              onClick={() => handleSupplyChain("downstream")}
              disabled={loading || !query.trim()}
              className="flex w-full items-center gap-2 rounded-xl bg-cyan-500/20 px-4 py-2.5 text-sm text-cyan-400 hover:bg-cyan-500/30 disabled:opacity-50"
            >
              <ArrowDownCircle className="h-4 w-4" />
              下游企业
            </button>
          </div>
          
          <h3 className="mb-3 mt-5 text-sm font-medium text-white">风险分析</h3>
          <button
            onClick={handleRiskAnalysis}
            disabled={loading || !query.trim()}
            className="flex w-full items-center gap-2 rounded-xl bg-red-500/20 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/30 disabled:opacity-50"
          >
            <AlertTriangle className="h-4 w-4" />
            风险传导分析
          </button>
        </div>
        
        {/* Node details */}
        {selectedNode && (
          <div className="rounded-2xl border border-white/10 bg-card/80 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-white">节点详情</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-500 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-slate-500 mb-1">名称</p>
                <p className="text-sm text-white">{selectedNode.name}</p>
              </div>
              
              <div>
                <p className="text-xs text-slate-500 mb-1">类型</p>
                <span
                  className="inline-block rounded-full px-2.5 py-1 text-xs font-medium"
                  style={{
                    backgroundColor: `${getNodeColor(selectedNode.type)}20`,
                    color: getNodeColor(selectedNode.type),
                  }}
                >
                  {selectedNode.type}
                </span>
              </div>
              
              {Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <p className="text-xs text-slate-500 mb-2">属性</p>
                  <div className="space-y-1.5">
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} className="flex text-xs">
                        <span className="text-slate-500 w-24">{key}</span>
                        <span className="text-slate-300 flex-1">
                          {typeof value === "object" ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Legend */}
        <div className="rounded-2xl border border-white/10 bg-card/80 p-4">
          <h3 className="mb-3 text-sm font-medium text-white">图例</h3>
          <div className="space-y-2">
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2 text-xs">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="text-slate-400">{type}</span>
              </div>
            ))}
          </div>
        </div>
        
        {/* Influence Ranking Panel */}
        <div className="rounded-2xl border border-white/10 bg-card/80 p-4">
          <div className="flex items-center gap-2 mb-3">
            <Trophy className="h-4 w-4 text-yellow-400" />
            <h3 className="text-sm font-medium text-white">影响力排名 Top 20</h3>
          </div>
          
          {loadingInfluence ? (
            <div className="text-xs text-slate-400">加载中...</div>
          ) : influenceData.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {influenceData.map((item, index) => (
                <div
                  key={`${item.name}-${index}`}
                  className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium w-5 ${
                      index < 3 ? "text-yellow-400" : "text-slate-500"
                    }`}>
                      {index + 1}
                    </span>
                    <span className="text-xs text-white truncate max-w-[120px]">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">{item.type}</span>
                    <span className="text-xs font-medium text-indigo-400">{item.score.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400">暂无数据</div>
          )}
        </div>
      </div>
    </div>
  );
}
