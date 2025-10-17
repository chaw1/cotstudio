import { KGEntity, KGRelation } from '../../types';

export interface CytoscapeNode {
  data: {
    id: string;
    label: string;
    type: string;
    properties: Record<string, any>;
    size?: number;
    color?: string;
  };
  position?: { x: number; y: number };
  classes?: string;
}

export interface CytoscapeEdge {
  data: {
    id: string;
    source: string;
    target: string;
    label: string;
    type: string;
    properties: Record<string, any>;
    weight?: number;
  };
  classes?: string;
}

export interface CytoscapeElement {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
}

export interface LayoutOptions {
  name: string;
  animate?: boolean;
  animationDuration?: number;
  fit?: boolean;
  padding?: number;
  [key: string]: any;
}

export interface FilterOptions {
  entityTypes: string[];
  relationTypes: string[];
  minConnections: number;
  maxNodes: number;
  searchQuery: string;
}

export interface ViewportState {
  zoom: number;
  pan: { x: number; y: number };
}

export interface KGVisualizationProps {
  projectId: string | null;
  height?: number | string;
  width?: number | string;
  initialLayout?: string;
  showControls?: boolean;
  showStats?: boolean;
  onNodeSelect?: (node: KGEntity) => void;
  onEdgeSelect?: (edge: KGRelation) => void;
  data?: {
    nodes: Array<{
      id: string;
      label: string;
      type?: string;
      [key: string]: any;
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      label?: string;
      type?: string;
      [key: string]: any;
    }>;
  };
  disableDataFetch?: boolean;
}

export interface NodeStyle {
  'background-color': string;
  'border-color': string;
  'border-width': number;
  'label': string;
  'text-valign': string;
  'text-halign': string;
  'font-size': number;
  'width': number;
  'height': number;
  'shape': string;
}

export interface EdgeStyle {
  'line-color': string;
  'target-arrow-color': string;
  'target-arrow-shape': string;
  'curve-style': string;
  'label': string;
  'font-size': number;
  'text-rotation': string;
  'width': number;
}