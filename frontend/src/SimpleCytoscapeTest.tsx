import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

const SimpleCytoscapeTest: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    console.log('Initializing simple cytoscape test');

    try {
      const cy = cytoscape({
        container: containerRef.current,
        elements: [
          { data: { id: 'a', label: '节点A' } },
          { data: { id: 'b', label: '节点B' } },
          { data: { id: 'c', label: '节点C' } },
          { data: { id: 'ab', source: 'a', target: 'b' } },
          { data: { id: 'bc', source: 'b', target: 'c' } }
        ],
        style: [
          {
            selector: 'node',
            style: {
              'content': 'data(label)',
              'text-valign': 'center',
              'color': '#fff',
              'background-color': '#1677ff',
              'font-size': '12px',
              'width': 40,
              'height': 40,
              'text-outline-width': 2,
              'text-outline-color': '#000'
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 2,
              'line-color': '#ccc',
              'target-arrow-color': '#ccc',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier'
            }
          }
        ],
        layout: {
          name: 'circle',
          fit: true,
          padding: 30
        }
      });

      console.log('Cytoscape instance created:', cy);
      
      // 添加点击事件测试
      cy.on('tap', 'node', (evt) => {
        const node = evt.target;
        console.log('Node clicked:', node.data());
      });

    } catch (error) {
      console.error('Failed to create cytoscape:', error);
    }
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h2>Cytoscape 简单测试</h2>
      <div 
        ref={containerRef}
        style={{ 
          width: '100%', 
          height: '400px', 
          border: '1px solid #ccc',
          backgroundColor: '#f5f5f5'
        }}
      />
    </div>
  );
};

export default SimpleCytoscapeTest;