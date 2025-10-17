import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const DirectCytoscapeTest: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) {
      console.log('Container not ready');
      return;
    }

    console.log('Starting direct cytoscape test...');

    try {
      const cy = cytoscape({
        container: containerRef.current,
        
        elements: [
          // 节点
          { data: { id: 'a', label: '用户A' } },
          { data: { id: 'b', label: '项目B' } },
          { data: { id: 'c', label: 'CoT数据' } },
          // 边
          { data: { source: 'a', target: 'b', label: '贡献' } },
          { data: { source: 'b', target: 'c', label: '包含' } }
        ],

        style: [
          {
            selector: 'node',
            style: {
              'content': 'data(label)',
              'text-valign': 'center',
              'text-halign': 'center',
              'color': 'white',
              'background-color': '#1677ff',
              'font-size': '14px',
              'width': 60,
              'height': 60,
              'text-outline-width': 2,
              'text-outline-color': '#000',
              'text-wrap': 'wrap',
              'text-max-width': '50px'
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 3,
              'line-color': '#ccc',
              'target-arrow-color': '#ccc',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'content': 'data(label)',
              'font-size': '10px',
              'text-rotation': 'autorotate',
              'text-background-color': 'white',
              'text-background-opacity': 0.8,
              'text-background-padding': '2px'
            }
          }
        ],

        layout: {
          name: 'circle',
          fit: true,
          padding: 30,
          radius: 80
        },

        // 启用交互
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: false,
        selectionType: 'single'
      });

      console.log('Cytoscape instance created successfully:', cy);
      
      // 绑定事件
      cy.on('tap', 'node', (event) => {
        const node = event.target;
        console.log('Node clicked:', node.data());
        // 高亮选中的节点
        cy.elements().removeClass('highlighted');
        node.addClass('highlighted');
      });

      // 适应视图
      setTimeout(() => {
        cy.fit();
      }, 100);

    } catch (error) {
      console.error('Failed to create cytoscape instance:', error);
    }
  }, []);

  return (
    <div style={{
      border: '2px solid #1677ff',
      borderRadius: '8px',
      padding: '10px',
      backgroundColor: '#f8f9fa'
    }}>
      <h3 style={{ margin: '0 0 10px 0', color: '#1677ff' }}>Cytoscape 直接测试</h3>
      <div 
        ref={containerRef}
        style={{ 
          width: '100%', 
          height: '300px', 
          border: '1px solid #d9d9d9',
          borderRadius: '4px',
          backgroundColor: 'white'
        }}
      />
    </div>
  );
};

export default DirectCytoscapeTest;