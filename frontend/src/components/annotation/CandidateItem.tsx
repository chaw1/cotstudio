import React, { useRef } from 'react';
import { Card, Input, Button, Space, Typography, Divider } from 'antd';
import { DeleteOutlined, DragOutlined } from '@ant-design/icons';
import { useDrag, useDrop } from 'react-dnd';
import RatingSlider from './RatingSlider';
import ChosenSelector from './ChosenSelector';
import { COTCandidate } from '../../stores/annotationStore';

const { TextArea } = Input;
const { Text } = Typography;

interface CandidateItemProps {
  candidate: COTCandidate;
  index: number;
  onUpdate: (updates: Partial<COTCandidate>) => void;
  onDelete: () => void;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  onSetChosen: (chosen: boolean) => void;
}

interface DragItem {
  index: number;
  id: string;
  type: string;
}

const CandidateItem: React.FC<CandidateItemProps> = ({
  candidate,
  index,
  onUpdate,
  onDelete,
  onMove,
  onSetChosen,
}) => {
  const ref = useRef<HTMLDivElement>(null);

  const [{ handlerId }, drop] = useDrop({
    accept: 'candidate',
    collect(monitor) {
      return {
        handlerId: monitor.getHandlerId(),
      };
    },
    hover(item: DragItem, monitor) {
      if (!ref.current) {
        return;
      }
      const dragIndex = item.index;
      const hoverIndex = index;

      // Don't replace items with themselves
      if (dragIndex === hoverIndex) {
        return;
      }

      // Determine rectangle on screen
      const hoverBoundingRect = ref.current?.getBoundingClientRect();

      // Get vertical middle
      const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;

      // Determine mouse position
      const clientOffset = monitor.getClientOffset();

      // Get pixels to the top
      const hoverClientY = (clientOffset?.y ?? 0) - hoverBoundingRect.top;

      // Only perform the move when the mouse has crossed half of the items height
      // When dragging downwards, only move when the cursor is below 50%
      // When dragging upwards, only move when the cursor is above 50%

      // Dragging downwards
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }

      // Dragging upwards
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }

      // Time to actually perform the action
      onMove(dragIndex, hoverIndex);

      // Note: we're mutating the monitor item here!
      // Generally it's better to avoid mutations,
      // but it's good here for the sake of performance
      // to avoid expensive index searches.
      item.index = hoverIndex;
    },
  });

  const [{ isDragging }, drag] = useDrag({
    type: 'candidate',
    item: () => {
      return { id: candidate.id, index };
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const opacity = isDragging ? 0.4 : 1;
  drag(drop(ref));

  return (
    <div ref={ref} style={{ opacity }} data-handler-id={handlerId}>
      <Card
        size="small"
        style={{
          border: candidate.chosen ? '2px solid #52c41a' : '1px solid #d9d9d9',
          backgroundColor: candidate.chosen ? '#f6ffed' : '#fff',
        }}
        title={
          <Space>
            <DragOutlined style={{ cursor: 'move', color: '#999' }} />
            <Text strong>候选答案 #{candidate.rank}</Text>
            {candidate.chosen && (
              <Text type="success" style={{ fontSize: '12px' }}>
                ✓ 已选择
              </Text>
            )}
          </Space>
        }
        extra={
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={onDelete}
            size="small"
          />
        }
      >
        <div style={{ marginBottom: '12px' }}>
          <Text strong style={{ fontSize: '13px' }}>答案内容:</Text>
          <TextArea
            value={candidate.text}
            onChange={(e) => onUpdate({ text: e.target.value })}
            placeholder="请输入答案内容..."
            rows={3}
            style={{ marginTop: '4px', resize: 'vertical' }}
          />
        </div>

        <div style={{ marginBottom: '12px' }}>
          <Text strong style={{ fontSize: '13px' }}>推理过程 (Chain of Thought):</Text>
          <TextArea
            value={candidate.chainOfThought}
            onChange={(e) => onUpdate({ chainOfThought: e.target.value })}
            placeholder="请输入详细的推理过程..."
            rows={4}
            style={{ marginTop: '4px', resize: 'vertical' }}
          />
        </div>

        <Divider style={{ margin: '12px 0' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ flex: 1, marginRight: '16px' }}>
            <RatingSlider
              value={candidate.score}
              onChange={(value) => onUpdate({ score: value })}
            />
          </div>
          
          <div>
            <ChosenSelector
              chosen={candidate.chosen}
              onChange={onSetChosen}
            />
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CandidateItem;