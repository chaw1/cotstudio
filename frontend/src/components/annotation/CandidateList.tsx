import React, { useCallback } from 'react';
import { Card, Button, Space, Typography, Empty } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import CandidateItem from './CandidateItem';
import { COTCandidate } from '../../stores/annotationStore';
// Simple ID generation function
const generateId = () => `candidate_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const { Title, Text } = Typography;

interface CandidateListProps {
  candidates: COTCandidate[];
  onChange: (candidates: COTCandidate[]) => void;
}

const CandidateList: React.FC<CandidateListProps> = ({
  candidates,
  onChange,
}) => {
  // 添加新的候选答案
  const handleAddCandidate = useCallback(() => {
    const newCandidate: COTCandidate = {
      id: generateId(),
      text: '',
      chainOfThought: '',
      score: 0.5,
      chosen: false,
      rank: candidates.length + 1,
    };
    onChange([...candidates, newCandidate]);
  }, [candidates, onChange]);

  // 更新候选答案
  const handleUpdateCandidate = useCallback((id: string, updates: Partial<COTCandidate>) => {
    const updatedCandidates = candidates.map(candidate =>
      candidate.id === id ? { ...candidate, ...updates } : candidate
    );
    onChange(updatedCandidates);
  }, [candidates, onChange]);

  // 删除候选答案
  const handleDeleteCandidate = useCallback((id: string) => {
    const filteredCandidates = candidates.filter(candidate => candidate.id !== id);
    // 重新排序
    const reorderedCandidates = filteredCandidates.map((candidate, index) => ({
      ...candidate,
      rank: index + 1,
    }));
    onChange(reorderedCandidates);
  }, [candidates, onChange]);

  // 移动候选答案位置
  const handleMoveCandidate = useCallback((dragIndex: number, hoverIndex: number) => {
    const draggedCandidate = candidates[dragIndex];
    const newCandidates = [...candidates];
    
    // 移除拖拽的项目
    newCandidates.splice(dragIndex, 1);
    // 在新位置插入
    newCandidates.splice(hoverIndex, 0, draggedCandidate);
    
    // 重新设置rank
    const reorderedCandidates = newCandidates.map((candidate, index) => ({
      ...candidate,
      rank: index + 1,
    }));
    
    onChange(reorderedCandidates);
  }, [candidates, onChange]);

  // 设置chosen状态（只能有一个chosen）
  const handleSetChosen = useCallback((id: string, chosen: boolean) => {
    const updatedCandidates = candidates.map(candidate => ({
      ...candidate,
      chosen: candidate.id === id ? chosen : false, // 确保只有一个chosen
    }));
    onChange(updatedCandidates);
  }, [candidates, onChange]);

  return (
    <Card size="small">
      <div style={{ marginBottom: '16px' }}>
        <Space>
          <Title level={5} style={{ margin: 0 }}>
            候选答案 ({candidates.length})
          </Title>
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={handleAddCandidate}
            size="small"
          >
            添加候选答案
          </Button>
        </Space>
        <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '4px' }}>
          拖拽调整顺序，设置评分，选择最佳答案（chosen）
        </Text>
      </div>

      {candidates.length === 0 ? (
        <Empty
          description="暂无候选答案"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          style={{ margin: '20px 0' }}
        >
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAddCandidate}>
            添加第一个候选答案
          </Button>
        </Empty>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {candidates
            .sort((a, b) => a.rank - b.rank)
            .map((candidate, index) => (
              <CandidateItem
                key={candidate.id}
                candidate={candidate}
                index={index}
                onUpdate={(updates) => handleUpdateCandidate(candidate.id, updates)}
                onDelete={() => handleDeleteCandidate(candidate.id)}
                onMove={handleMoveCandidate}
                onSetChosen={(chosen) => handleSetChosen(candidate.id, chosen)}
              />
            ))}
        </div>
      )}

      {candidates.length > 0 && (
        <div style={{ marginTop: '16px', padding: '12px', background: '#f9f9f9', borderRadius: '4px' }}>
          <Text strong style={{ fontSize: '12px' }}>标注统计:</Text>
          <div style={{ marginTop: '4px' }}>
            <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
              <Text style={{ fontSize: '12px' }}>
                总数: {candidates.length}
              </Text>
              <Text style={{ fontSize: '12px' }}>
                已选择: {candidates.filter(c => c.chosen).length}
              </Text>
              <Text style={{ fontSize: '12px' }}>
                平均分: {candidates.length > 0 ? (candidates.reduce((sum, c) => sum + c.score, 0) / candidates.length).toFixed(2) : '0.00'}
              </Text>
            </Space>
          </div>
        </div>
      )}
    </Card>
  );
};

export default CandidateList;