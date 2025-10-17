import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, Row, Col, Spin } from 'antd';
import cytoscape, { Core, NodeSingular, EdgeSingular } from 'cytoscape';
import safeMessage from '../../utils/message';
import './KnowledgeGraphViewer.css';

// 简化扩展加载，直接使用基础布局
let extensionsLoaded = false;

// 简化的扩展加载函数
const loadCytoscapeExtensions = async () => {
  if (extensionsLoaded) return;
  
  // 暂时跳过扩展加载，直接使用基础布局
  console.log('Using basic Cytoscape layouts only');
  extensionsLoaded = true;
};

import knowledgeGraphService from '../../services/knowledgeGraphService';
import { KGEntity, KGRelation } from '../../types';
import { 
  CytoscapeElement, 
  CytoscapeNode, 
  CytoscapeEdge, 
  FilterOptions, 
  ViewportState,
  KGVisualizationProps 
} from './types';
import KGControlPanel from './KGControlPanel';
import KGEntityPanel from './KGEntityPanel';
import KGSearchPanel from './KGSearchPanel';
import KGStatsPanel from './KGStatsPanel';

// 扩展将在组件中动态加载

// 获取安全的布局名称
const getSafeLayout = (layout: string): string => {
  const safeLayouts = ['cose', 'circle', 'grid', 'random', 'concentric', 'breadthfirst'];
  return safeLayouts.includes(layout) ? layout : 'cose';
};

const KnowledgeGraphViewer: React.FC<KGVisualizationProps> = ({
  projectId,
  height = 600,
  width,
  initialLayout = 'cose', // 使用基础布局
  showControls = true,
  showStats = true,
  onNodeSelect,
  onEdgeSelect,
  data,
  disableDataFetch = false
}) => {
  const cyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<Core | null>(null);
  const isMountedRef = useRef(true);
  const initializationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const layoutTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const [loading, setLoading] = useState(false); // 默认不加载，由useEffect控制
  const [entities, setEntities] = useState<KGEntity[]>([]);
  const [relations, setRelations] = useState<KGRelation[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<KGEntity | null>(null);
  const [selectedRelation, setSelectedRelation] = useState<KGRelation | null>(null);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    entityTypes: [],
    relationTypes: [],
    minConnections: 0,
    maxNodes: 100,
    searchQuery: ''
  });
  const [viewport, setViewport] = useState<ViewportState>({
    zoom: 1,
    pan: { x: 0, y: 0 }
  });
  const [currentLayout, setCurrentLayout] = useState(initialLayout);

  // 将KG数据转换为Cytoscape格式
  const convertToElements = useCallback((entities: KGEntity[], relations: KGRelation[]): CytoscapeElement => {
    const nodes: CytoscapeNode[] = entities.map(entity => ({
      data: {
        id: entity.id,
        label: entity.label,
        type: entity.type,
        properties: entity.properties,
        // 优先使用外部传入的size和color，如果没有则使用默认计算
        size: entity.properties.originalSize || entity.properties.size || Math.max(20, Math.min(60, (entity.properties.connections || 1) * 5)),
        color: entity.properties.originalColor || entity.properties.color || getEntityColor(entity.type)
      },
      classes: `entity-${entity.type.toLowerCase().replace(/\s+/g, '-')}`
    }));

    const edges: CytoscapeEdge[] = relations.map(relation => ({
      data: {
        id: relation.id,
        source: relation.source,
        target: relation.target,
        label: relation.type,
        type: relation.type,
        properties: relation.properties,
        weight: relation.properties.weight || 1,
        // 使用外部传入的颜色
        color: relation.properties.originalColor || relation.properties.color || '#d9d9d9'
      },
      classes: `relation-${relation.type.toLowerCase().replace(/\s+/g, '-')}`
    }));

    return { nodes, edges };
  }, []);

  // 获取实体类型颜色
  const getEntityColor = (type: string): string => {
    const colors: Record<string, string> = {
      'Person': '#FF6B6B',
      'Organization': '#4ECDC4',
      'Location': '#45B7D1',
      'Concept': '#96CEB4',
      'Event': '#FFEAA7',
      'Document': '#DDA0DD',
      'Technology': '#98D8C8',
      'default': '#BDC3C7'
    };
    return colors[type] || colors.default;
  };

  // 获取Cytoscape样式
  const getCytoscapeStyle = () => [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'border-color': '#2c3e50',
        'border-width': 2,
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '12px',
        'font-weight': 'bold',
        'color': '#2c3e50',
        'text-outline-width': 2,
        'text-outline-color': '#ffffff',
        'width': 'data(size)',
        'height': 'data(size)',
        'shape': 'ellipse'
      }
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': '#e74c3c',
        'background-color': '#ecf0f1'
      }
    },
    {
      selector: 'edge',
      style: {
        'line-color': 'data(color)',
        'target-arrow-color': 'data(color)',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '10px',
        'text-rotation': 'autorotate',
        'text-margin-y': -10,
        'width': 2
      }
    },
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#e74c3c',
        'target-arrow-color': '#e74c3c',
        'width': 3
      }
    },
    {
      selector: '.highlighted',
      style: {
        'background-color': '#f39c12',
        'line-color': '#f39c12',
        'target-arrow-color': '#f39c12',
        'transition-property': 'background-color, line-color, target-arrow-color',
        'transition-duration': '0.5s'
      }
    }
  ];

  // 安全的状态更新函数
  const safeSetState = useCallback((setter: () => void) => {
    if (isMountedRef.current) {
      try {
        setter();
      } catch (error) {
        console.warn('State update failed:', error);
      }
    }
  }, []);

  // 清理Cytoscape实例
  const cleanupCytoscape = useCallback(() => {
    try {
      if (cyInstance.current) {
        // 移除所有事件监听器
        cyInstance.current.removeAllListeners();
        // 停止所有正在运行的布局
        cyInstance.current.elements().stop();
        // 销毁实例
        cyInstance.current.destroy();
        cyInstance.current = null;
      }
    } catch (error) {
      console.warn('Error during cytoscape cleanup:', error);
      // 强制设置为null，即使销毁失败
      cyInstance.current = null;
    }
  }, []);

  // 初始化Cytoscape
  const initializeCytoscape = useCallback((elements: CytoscapeElement) => {
    // 检查组件是否仍然挂载
    if (!isMountedRef.current || !cyRef.current) {
      console.warn('[KnowledgeGraphViewer] 组件已卸载或容器未准备好');
      setLoading(false);
      return;
    }

    try {
      // 清理现有实例
      cleanupCytoscape();

      // 检查元素数量，避免创建空图
      if (elements.nodes.length === 0) {
        console.log('[KnowledgeGraphViewer] 没有节点数据，停止加载');
        setLoading(false);
        return;
      }

      console.log('[KnowledgeGraphViewer] 开始初始化Cytoscape:', {
        nodes: elements.nodes.length,
        edges: elements.edges.length,
        containerWidth: cyRef.current.offsetWidth,
        containerHeight: cyRef.current.offsetHeight
      });

      cyInstance.current = cytoscape({
        container: cyRef.current,
        elements: [...elements.nodes, ...elements.edges],
        style: getCytoscapeStyle() as any,
        layout: {
          name: getSafeLayout(currentLayout), // 使用配置的安全布局
          fit: true,
          padding: 30,
          animate: false
        } as any,
        wheelSensitivity: 1,
        minZoom: 0.1,
        maxZoom: 3,
        userZoomingEnabled: true,
        userPanningEnabled: true
      });

      console.log('[KnowledgeGraphViewer] Cytoscape实例创建成功:', {
        instance: !!cyInstance.current,
        nodesCount: cyInstance.current?.nodes().length,
        edgesCount: cyInstance.current?.edges().length
      });
      
      // 输出所有节点和边的信息用于调试
      if (cyInstance.current) {
        console.log('[KnowledgeGraphViewer] 所有节点:', cyInstance.current.nodes().map(n => ({
          id: n.data('id'),
          label: n.data('label'),
          size: n.data('size'),
          color: n.data('color')
        })));
        console.log('[KnowledgeGraphViewer] 所有边:', cyInstance.current.edges().map(e => ({
          id: e.data('id'),
          source: e.data('source'),
          target: e.data('target'),
          color: e.data('color')
        })));
      }

      // 绑定事件
      if (cyInstance.current) {
        cyInstance.current.on('tap', 'node', (event) => {
          if (!isMountedRef.current) return;
          
          const node = event.target as NodeSingular;
          const entityId = node.data('id');
          const entity = entities.find(e => e.id === entityId);
          
          if (entity) {
            setSelectedEntity(entity);
            setSelectedRelation(null);
            onNodeSelect?.(entity);
          }
        });

        cyInstance.current.on('tap', 'edge', (event) => {
          if (!isMountedRef.current) return;
          
          const edge = event.target as EdgeSingular;
          const relationId = edge.data('id');
          const relation = relations.find(r => r.id === relationId);
          
          if (relation) {
            setSelectedRelation(relation);
            setSelectedEntity(null);
            onEdgeSelect?.(relation);
          }
        });
      }

      console.log('Cytoscape initialized successfully');
      
      // 立即停止加载状态
      if (isMountedRef.current) {
        setLoading(false);
      }

    } catch (error) {
      console.error('Failed to initialize cytoscape:', error);
      if (isMountedRef.current) {
        safeMessage.error('知识图谱初始化失败');
        safeSetState(() => setLoading(false));
      }
    }
  }, [entities, relations, currentLayout, onNodeSelect, onEdgeSelect, cleanupCytoscape, safeSetState]);

  // 加载知识图谱数据
  const loadKnowledgeGraph = useCallback(async () => {
    if (!isMountedRef.current) return;
    
    try {
      // 清理之前的超时
      if (initializationTimeoutRef.current) {
        clearTimeout(initializationTimeoutRef.current);
        initializationTimeoutRef.current = null;
      }
      
      // 使用ref获取最新值，避免依赖变化导致无限循环
      const currentData = dataRef.current;
      const currentDisableDataFetch = disableDataFetchRef.current;
      const currentProjectId = projectIdRef.current;
      
      // 如果禁用数据获取或提供了外部数据，使用外部数据
      if (currentDisableDataFetch || currentData) {
        console.log('[KnowledgeGraphViewer] 使用外部数据模式, disableDataFetch:', currentDisableDataFetch, 'hasData:', !!currentData);
        if (currentData && currentData.nodes && currentData.edges && isMountedRef.current) {
          console.log('[KnowledgeGraphViewer] 接收到外部数据:', {
            nodes: currentData.nodes.length,
            edges: currentData.edges.length,
            firstNode: currentData.nodes[0],
            firstEdge: currentData.edges[0]
          });
          
          // 转换外部数据格式为内部格式
          const mockEntities: KGEntity[] = currentData.nodes.map(node => ({
            id: String(node.id),
            label: String(node.label || node.id),
            type: String(node.type || 'default'),
            properties: { 
              ...node.data,
              size: node.size || 30,
              color: node.color || '#1677ff',
              // 保留原始size和color供后续使用
              originalSize: node.size || 30,
              originalColor: node.color || '#1677ff'
            }
          }));
          
          const mockRelations: KGRelation[] = currentData.edges.map(edge => ({
            id: String(edge.id),
            source: String(edge.source),
            target: String(edge.target),
            type: String(edge.type || 'related'),
            properties: { 
              color: edge.color || '#d9d9d9',
              originalColor: edge.color || '#d9d9d9'
            }
          }));
          
          console.log('[KnowledgeGraphViewer] 转换后的内部数据:', {
            entities: mockEntities.length,
            relations: mockRelations.length
          });
          
          // 立即设置数据
          setEntities(mockEntities);
          setRelations(mockRelations);
          
          const elements = convertToElements(mockEntities, mockRelations);
          console.log('[KnowledgeGraphViewer] Cytoscape元素:', {
            nodes: elements.nodes.length,
            edges: elements.edges.length,
            firstNode: elements.nodes[0],
            firstEdge: elements.edges[0]
          });
          
          // 验证元素格式
          if (elements.nodes.length > 0) {
            console.log('[KnowledgeGraphViewer] 第一个节点详细信息:', {
              id: elements.nodes[0].data.id,
              label: elements.nodes[0].data.label,
              size: elements.nodes[0].data.size,
              color: elements.nodes[0].data.color,
              type: elements.nodes[0].data.type
            });
          }
          
          // 延迟初始化确保DOM准备就绪
          setTimeout(() => {
            if (isMountedRef.current && cyRef.current) {
              console.log('[KnowledgeGraphViewer] 准备初始化Cytoscape实例...');
              initializeCytoscape(elements);
            } else {
              console.warn('[KnowledgeGraphViewer] 组件已卸载或容器未准备好');
            }
          }, 150);
        } else {
          console.warn('[KnowledgeGraphViewer] 无效的外部数据:', {
            hasData: !!data,
            hasNodes: data?.nodes,
            hasEdges: data?.edges,
            isMounted: isMountedRef.current
          });
        }
        
        if (isMountedRef.current) {
          setLoading(false);
        }
        return;
      }
      
      // 如果没有有效的项目ID，不加载数据
      if (!currentProjectId) {
        console.log('No project ID, showing empty state');
        safeSetState(() => {
          setEntities([]);
          setRelations([]);
          setLoading(false);
        });
        return;
      }
      
      // 只有在需要从API获取数据时才设置loading
      safeSetState(() => setLoading(true));
      
      const graphData = await knowledgeGraphService.getKnowledgeGraph(currentProjectId, {
        entityTypes: filterOptions.entityTypes.length > 0 ? filterOptions.entityTypes : undefined,
        relationTypes: filterOptions.relationTypes.length > 0 ? filterOptions.relationTypes : undefined,
        limit: filterOptions.maxNodes,
        search: filterOptions.searchQuery || undefined
      });
      
      if (!isMountedRef.current) return;
      
      safeSetState(() => {
        setEntities(graphData.entities);
        setRelations(graphData.relations);
      });
      
      const elements = convertToElements(graphData.entities, graphData.relations);
      
      // 立即初始化，不使用延迟
      if (isMountedRef.current && cyRef.current) {
        initializeCytoscape(elements);
      }
      
    } catch (error) {
      console.error('Failed to load knowledge graph:', error);
      if (isMountedRef.current) {
        safeMessage.error('加载知识图谱失败');
      }
    } finally {
      if (isMountedRef.current) {
        safeSetState(() => setLoading(false));
      }
    }
  }, [convertToElements, initializeCytoscape, safeSetState]); // 移除会导致无限循环的依赖

  // 应用布局
  const applyLayout = useCallback((layoutName: string) => {
    if (!isMountedRef.current || !cyInstance.current) return;
    
    try {
      // 清理之前的布局超时
      if (layoutTimeoutRef.current) {
        clearTimeout(layoutTimeoutRef.current);
        layoutTimeoutRef.current = null;
      }
      
      const safeLayoutName = getSafeLayout(layoutName);
      safeSetState(() => setCurrentLayout(safeLayoutName));
      
      // 停止当前运行的布局
      cyInstance.current.elements().stop();
      
      const layout = cyInstance.current.layout({
        name: safeLayoutName,
        fit: true,
        padding: 50,
        animate: false // 禁用动画避免状态冲突
      } as any);
      
      // 延迟运行布局，避免冲突
      layoutTimeoutRef.current = setTimeout(() => {
        if (isMountedRef.current && cyInstance.current) {
          try {
            layout.run();
          } catch (error) {
            console.warn('Layout execution failed:', error);
          }
        }
      }, 50);
      
    } catch (error) {
      console.error('Failed to apply layout:', error);
    }
  }, [safeSetState]);

  // 高亮节点
  const highlightNodes = useCallback((nodeIds: string[]) => {
    if (!isMountedRef.current || !cyInstance.current) {
      console.warn('Cytoscape instance not available for highlighting');
      return;
    }
    
    try {
      cyInstance.current.elements().removeClass('highlighted');
      
      nodeIds.forEach(nodeId => {
        if (!isMountedRef.current || !cyInstance.current) return;
        
        const node = cyInstance.current.getElementById(nodeId);
        if (node.length > 0) {
          node.addClass('highlighted');
          
          // 高亮相关边
          node.connectedEdges().addClass('highlighted');
        }
      });
    } catch (error) {
      console.error('Error highlighting nodes:', error);
    }
  }, []);

  // 搜索并高亮
  const handleSearch = useCallback((query: string) => {
    if (!isMountedRef.current || !cyInstance.current) {
      console.warn('Cytoscape instance not available for search');
      return;
    }
    
    try {
      if (!query.trim()) {
        cyInstance.current.elements().removeClass('highlighted');
        return;
      }
      
      const matchingNodes = entities.filter(entity => 
        entity.label.toLowerCase().includes(query.toLowerCase()) ||
        entity.type.toLowerCase().includes(query.toLowerCase())
      );
      
      highlightNodes(matchingNodes.map(node => node.id));
      
      if (matchingNodes.length > 0 && isMountedRef.current && cyInstance.current) {
        const nodeIds = matchingNodes.map(node => node.id);
        const nodes = cyInstance.current.nodes().filter(node => 
          nodeIds.includes(node.data('id'))
        );
        cyInstance.current.fit(nodes, 50);
      }
    } catch (error) {
      console.error('Error during search:', error);
    }
  }, [entities, highlightNodes]);

  // 缩放控制
  const zoomIn = useCallback(() => {
    if (!isMountedRef.current || !cyInstance.current) return;
    
    try {
      const currentZoom = cyInstance.current.zoom();
      const newZoom = Math.min(currentZoom * 1.2, 5);
      cyInstance.current.zoom(newZoom);
    } catch (error) {
      console.warn('Error zooming in:', error);
    }
  }, []);

  const zoomOut = useCallback(() => {
    if (!isMountedRef.current || !cyInstance.current) return;
    
    try {
      const currentZoom = cyInstance.current.zoom();
      const newZoom = Math.max(currentZoom * 0.8, 0.05);
      cyInstance.current.zoom(newZoom);
    } catch (error) {
      console.warn('Error zooming out:', error);
    }
  }, []);

  const fitToView = useCallback(() => {
    if (!isMountedRef.current || !cyInstance.current) return;
    
    try {
      cyInstance.current.fit(undefined, 50);
    } catch (error) {
      console.warn('Error fitting to view:', error);
    }
  }, []);

  // 重置视图
  const resetView = useCallback(() => {
    if (!isMountedRef.current || !cyInstance.current) {
      console.warn('Cytoscape instance not available for reset');
      return;
    }
    
    try {
      cyInstance.current.fit();
      cyInstance.current.elements().removeClass('highlighted');
      safeSetState(() => {
        setSelectedEntity(null);
        setSelectedRelation(null);
      });
    } catch (error) {
      console.error('Error resetting view:', error);
    }
  }, [safeSetState]);

  // 导出图片
  const exportImage = useCallback((format: 'png' | 'jpg' = 'png') => {
    if (!isMountedRef.current || !cyInstance.current) {
      console.warn('Cytoscape instance not available for export');
      return;
    }
    
    try {
      const dataUrl = cyInstance.current.png({
        output: 'blob',
        bg: '#ffffff',
        full: true,
        scale: 2
      });
      
      const link = document.createElement('a');
      link.download = `knowledge-graph.${format}`;
      link.href = URL.createObjectURL(dataUrl);
      link.click();
    } catch (error) {
      console.error('Error exporting image:', error);
      if (isMountedRef.current) {
        safeMessage.error('导出图片失败');
      }
    }
  }, []);

  // 加载Cytoscape扩展
  useEffect(() => {
    loadCytoscapeExtensions();
  }, []);

  // 初始化 - 使用dataRef来避免无限循环
  const dataRef = useRef(data);
  const disableDataFetchRef = useRef(disableDataFetch);
  const projectIdRef = useRef(projectId);
  
  useEffect(() => {
    dataRef.current = data;
    disableDataFetchRef.current = disableDataFetch;
    projectIdRef.current = projectId;
  });

  // 初始化 - 只在首次挂载和关键依赖变化时执行
  useEffect(() => {
    // 延迟初始化，确保DOM元素完全准备好
    const timer = setTimeout(() => {
      loadKnowledgeGraph();
    }, 100);
    
    return () => clearTimeout(timer);
  }, []); // 空依赖数组，只在首次挂载时执行

  // 清理
  useEffect(() => {
    return () => {
      // 标记组件为已卸载
      isMountedRef.current = false;
      
      // 清理所有超时
      if (initializationTimeoutRef.current) {
        clearTimeout(initializationTimeoutRef.current);
        initializationTimeoutRef.current = null;
      }
      
      if (layoutTimeoutRef.current) {
        clearTimeout(layoutTimeoutRef.current);
        layoutTimeoutRef.current = null;
      }
      
      // 清理Cytoscape实例
      cleanupCytoscape();
    };
  }, [cleanupCytoscape]);

  // 调试日志
  console.log('[KnowledgeGraphViewer] Render state:', {
    loading,
    entitiesCount: entities.length,
    relationsCount: relations.length,
    disableDataFetch,
    hasData: !!data,
    projectId
  });

  return (
    <div style={{ height: '100%', width: '100%', display: 'flex', gap: '12px' }}>
      {/* 控制面板 */}
      {showControls && (
        <div style={{ 
          width: '320px', 
          height: '100%', 
          overflowY: 'auto',
          flexShrink: 0
        }}>
          <KGSearchPanel
            onSearch={handleSearch}
            onFilter={setFilterOptions}
            filterOptions={filterOptions}
            entities={entities}
            relations={relations}
          />
          
          <KGControlPanel
            currentLayout={currentLayout}
            onLayoutChange={applyLayout}
            onReset={resetView}
            onExport={exportImage}
            viewport={viewport}
            nodeCount={entities.length}
            edgeCount={relations.length}
            onZoomIn={zoomIn}
            onZoomOut={zoomOut}
            onFitToView={fitToView}
          />
          
          {showStats && (
            <KGStatsPanel projectId={projectId} />
          )}
        </div>
      )}
      
      {/* 图谱可视化区域 */}
      <div style={{ 
        flex: 1, 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        minWidth: 0 // 防止 flex 子元素溢出
      }}>
        {showControls ? (
          <Card 
            title="知识图谱" 
            style={{ 
              height: '100%',
              display: 'flex',
              flexDirection: 'column'
            }}
            styles={{ 
              body: { 
                padding: '8px', 
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                overflow: 'hidden'
              },
              header: {
                padding: '12px 16px',
                minHeight: '48px'
              }
            }}
          >
            <Spin 
              spinning={loading}
              style={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <div className="kg-container" style={{ 
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div
                  ref={cyRef}
                  style={{
                    width: '100%',
                    height: '100%',
                    border: '1px solid #e8e8e8',
                    borderRadius: '4px',
                    backgroundColor: '#fafafa'
                  }}
                />
                <div className="kg-scroll-hint" style={{
                  position: 'absolute',
                  bottom: '16px',
                  right: '16px',
                  fontSize: '12px',
                  color: '#666',
                  backgroundColor: 'rgba(255,255,255,0.95)',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  border: '1px solid #e8e8e8'
                }}>
                  💡 使用滚轮缩放，拖拽移动视图
                </div>
              </div>
            </Spin>
          </Card>
        ) : (
          <Spin 
            spinning={loading}
            style={{ 
              height: '100%',
              width: '100%'
            }}
          >
            <div
              ref={cyRef}
              style={{
                width: '100%',
                height: typeof height === 'number' ? `${height}px` : (height || '100%'),
                minHeight: typeof height === 'number' ? height : 400,
                position: 'relative',
                backgroundColor: '#fafafa'
              }}
            />
          </Spin>
        )}
      </div>
      
      {/* 详情面板 */}
      {showControls && (selectedEntity || selectedRelation) && (
        <div style={{ 
          width: '320px', 
          height: '100%',
          flexShrink: 0
        }}>
          <KGEntityPanel
            entity={selectedEntity}
            relation={selectedRelation}
            onClose={() => {
              safeSetState(() => {
                setSelectedEntity(null);
                setSelectedRelation(null);
              });
            }}
            onHighlightNeighbors={(entityId) => {
              // 高亮邻居节点
              if (cyInstance.current) {
                const node = cyInstance.current.getElementById(entityId);
                const neighbors = node.neighborhood().nodes();
                const neighborIds = neighbors.map(n => n.data('id'));
                highlightNodes([entityId, ...neighborIds]);
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraphViewer;