import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, message, Spin, Typography, Space, Divider } from 'antd';
import { SaveOutlined, ReloadOutlined, PlusOutlined } from '@ant-design/icons';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import TextSelector from './TextSelector';
import QuestionGenerator from './QuestionGenerator';
import CandidateList from './CandidateList';
import useAnnotation from '../../hooks/useAnnotation';
import { COTCandidate } from '../../stores/annotationStore';

const { Title, Text } = Typography;

interface AnnotationWorkspaceProps {
  projectId: string;
  sliceId?: string;
}

const AnnotationWorkspace: React.FC<AnnotationWorkspaceProps> = ({
  projectId,
  sliceId: initialSliceId
}) => {
  const [selectedText, setSelectedText] = useState<string>('');
  const [question, setQuestion] = useState<string>('');
  const [candidates, setCandidates] = useState<COTCandidate[]>([]);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false);

  const {
    currentCOTItem,
    selectedSliceId,
    loading,
    generateQuestionLoading,
    generateCandidatesLoading,
    createCOTItem,
    updateCOTItem,
    generateQuestion,
    generateCandidates,
    selectSlice,
    selectCOTItem,
  } = useAnnotation(projectId);

  // 初始化选中的切片
  useEffect(() => {
    if (initialSliceId && initialSliceId !== selectedSliceId) {
      selectSlice(initialSliceId);
    }
  }, [initialSliceId, selectedSliceId, selectSlice]);

  // 当选择新的CoT项时，更新本地状态
  useEffect(() => {
    if (currentCOTItem) {
      setQuestion(currentCOTItem.question);
      setCandidates(currentCOTItem.candidates);
      setIsEditing(true);
      setHasUnsavedChanges(false);
    } else {
      setQuestion('');
      setCandidates([]);
      setIsEditing(false);
      setHasUnsavedChanges(false);
    }
  }, [currentCOTItem]);

  // 处理文本选择
  const handleTextSelection = (text: string) => {
    setSelectedText(text);
    setHasUnsavedChanges(true);
  };

  // 生成问题
  const handleGenerateQuestion = async () => {
    if (!selectedSliceId) {
      message.warning('请先选择文本切片');
      return;
    }

    try {
      const generatedQuestion = await generateQuestion(selectedSliceId);
      if (generatedQuestion) {
        setQuestion(generatedQuestion);
        setHasUnsavedChanges(true);
        message.success('问题生成成功');
      }
    } catch (error) {
      message.error('问题生成失败');
    }
  };

  // 生成候选答案
  const handleGenerateCandidates = async () => {
    if (!question.trim()) {
      message.warning('请先输入或生成问题');
      return;
    }

    if (!selectedSliceId) {
      message.warning('请先选择文本切片');
      return;
    }

    try {
      const generatedCandidates = await generateCandidates(question, selectedSliceId);
      if (generatedCandidates && generatedCandidates.length > 0) {
        setCandidates(generatedCandidates);
        setHasUnsavedChanges(true);
        message.success(`生成了 ${generatedCandidates.length} 个候选答案`);
      }
    } catch (error) {
      message.error('候选答案生成失败');
    }
  };

  // 更新候选答案
  const handleCandidatesChange = (updatedCandidates: COTCandidate[]) => {
    setCandidates(updatedCandidates);
    setHasUnsavedChanges(true);
  };

  // 保存CoT数据
  const handleSave = async () => {
    if (!question.trim()) {
      message.warning('请输入问题');
      return;
    }

    if (candidates.length === 0) {
      message.warning('请添加至少一个候选答案');
      return;
    }

    if (!selectedSliceId) {
      message.warning('请选择文本切片');
      return;
    }

    try {
      const data = {
        projectId,
        sliceId: selectedSliceId,
        question: question.trim(),
        candidates: candidates.map(({ id, ...rest }) => rest), // 移除id，让后端生成
      };

      let result;
      if (isEditing && currentCOTItem) {
        result = await updateCOTItem(currentCOTItem.id, {
          question: question.trim(),
          candidates,
        });
      } else {
        result = await createCOTItem(data);
      }

      if (result) {
        setHasUnsavedChanges(false);
        message.success(isEditing ? 'CoT数据更新成功' : 'CoT数据创建成功');
        selectCOTItem(result);
      }
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 重置表单
  const handleReset = () => {
    if (currentCOTItem) {
      setQuestion(currentCOTItem.question);
      setCandidates(currentCOTItem.candidates);
    } else {
      setQuestion('');
      setCandidates([]);
    }
    setSelectedText('');
    setHasUnsavedChanges(false);
  };

  // 创建新的标注
  const handleCreateNew = () => {
    selectCOTItem(null);
    setQuestion('');
    setCandidates([]);
    setSelectedText('');
    setIsEditing(false);
    setHasUnsavedChanges(false);
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div style={{ height: '100%', background: '#f5f5f5', padding: '16px' }}>
        {/* 工具栏 */}
        <Card style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={4} style={{ margin: 0 }}>
              CoT标注工作台
            </Title>
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleCreateNew}
                disabled={loading}
              >
                新建标注
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                disabled={loading || !hasUnsavedChanges}
                loading={loading}
              >
                保存
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={handleReset}
                disabled={loading}
              >
                重置
              </Button>
              {hasUnsavedChanges && (
                <Text type="warning">
                  有未保存的更改
                </Text>
              )}
            </Space>
          </div>
        </Card>

        {/* 主要内容区域 */}
        <Row gutter={16} style={{ height: 'calc(100% - 100px)' }}>
          {/* 左侧：文本选择区域 */}
          <Col span={8}>
            <Card 
              title="文本选择" 
              style={{ height: '100%' }}
              styles={{ 
                body: {
                  height: 'calc(100% - 57px)', 
                  overflow: 'auto',
                  padding: '16px'
                }
              }}
            >
              <TextSelector
                projectId={projectId}
                selectedSliceId={selectedSliceId}
                onTextSelect={handleTextSelection}
                onSliceSelect={selectSlice}
              />
              
              {selectedText && (
                <Card size="small" style={{ marginTop: '16px' }}>
                  <Text strong>选中文本:</Text>
                  <div style={{ 
                    marginTop: '8px', 
                    padding: '8px', 
                    background: '#f0f0f0', 
                    borderRadius: '4px',
                    maxHeight: '120px',
                    overflow: 'auto'
                  }}>
                    <Text>{selectedText}</Text>
                  </div>
                </Card>
              )}
            </Card>
          </Col>

          {/* 右侧：标注工作区域 */}
          <Col span={16}>
            <Card 
              title="标注编辑" 
              style={{ height: '100%' }}
              styles={{ 
                body: {
                  height: 'calc(100% - 57px)', 
                  overflow: 'auto',
                  padding: '16px'
                }
              }}
            >
              <Spin spinning={loading}>
                <div style={{ marginBottom: '24px' }}>
                  <QuestionGenerator
                    question={question}
                    onQuestionChange={(value) => {
                      setQuestion(value);
                      setHasUnsavedChanges(true);
                    }}
                    onGenerate={handleGenerateQuestion}
                    loading={generateQuestionLoading}
                    disabled={!selectedSliceId}
                  />
                </div>

                <Divider />

                <div style={{ marginBottom: '24px' }}>
                  <div style={{ marginBottom: '16px' }}>
                    <Space>
                      <Title level={5} style={{ margin: 0 }}>候选答案</Title>
                      <Button
                        type="dashed"
                        onClick={handleGenerateCandidates}
                        loading={generateCandidatesLoading}
                        disabled={!question.trim() || !selectedSliceId}
                      >
                        生成候选答案
                      </Button>
                    </Space>
                  </div>

                  <CandidateList
                    candidates={candidates}
                    onChange={handleCandidatesChange}
                  />
                </div>
              </Spin>
            </Card>
          </Col>
        </Row>
      </div>
    </DndProvider>
  );
};

export default AnnotationWorkspace;