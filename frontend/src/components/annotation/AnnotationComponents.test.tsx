import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { BrowserRouter } from 'react-router-dom';
import AnnotationWorkspace from './AnnotationWorkspace';
import TextSelector from './TextSelector';
import QuestionGenerator from './QuestionGenerator';
import CandidateList from './CandidateList';
import CandidateItem from './CandidateItem';
import RatingSlider from './RatingSlider';
import ChosenSelector from './ChosenSelector';
import { COTCandidate } from '../../stores/annotationStore';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock hooks
vi.mock('../../hooks/useAnnotation', () => ({
  default: vi.fn(() => ({
    currentCOTItem: null,
    selectedSliceId: null,
    loading: false,
    generateQuestionLoading: false,
    generateCandidatesLoading: false,
    createCOTItem: vi.fn(),
    updateCOTItem: vi.fn(),
    generateQuestion: vi.fn(),
    generateCandidates: vi.fn(),
    selectSlice: vi.fn(),
    selectCOTItem: vi.fn(),
  })),
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <DndProvider backend={HTML5Backend}>
      {children}
    </DndProvider>
  </BrowserRouter>
);

describe('Annotation Components', () => {
  describe('QuestionGenerator', () => {
    it('renders question input and generate button', () => {
      const mockProps = {
        question: '',
        onQuestionChange: vi.fn(),
        onGenerate: vi.fn(),
        loading: false,
        disabled: false,
      };

      render(<QuestionGenerator {...mockProps} />);

      expect(screen.getByPlaceholderText(/请输入问题/)).toBeInTheDocument();
      expect(screen.getByText('AI生成问题')).toBeInTheDocument();
    });

    it('calls onQuestionChange when input changes', () => {
      const mockOnChange = vi.fn();
      const mockProps = {
        question: '',
        onQuestionChange: mockOnChange,
        onGenerate: vi.fn(),
        loading: false,
        disabled: false,
      };

      render(<QuestionGenerator {...mockProps} />);

      const input = screen.getByPlaceholderText(/请输入问题/);
      fireEvent.change(input, { target: { value: 'Test question' } });

      expect(mockOnChange).toHaveBeenCalledWith('Test question');
    });

    it('calls onGenerate when generate button is clicked', () => {
      const mockOnGenerate = vi.fn();
      const mockProps = {
        question: '',
        onQuestionChange: vi.fn(),
        onGenerate: mockOnGenerate,
        loading: false,
        disabled: false,
      };

      render(<QuestionGenerator {...mockProps} />);

      const generateButton = screen.getByText('AI生成问题');
      fireEvent.click(generateButton);

      expect(mockOnGenerate).toHaveBeenCalled();
    });
  });

  describe('RatingSlider', () => {
    it('renders slider with correct initial value', () => {
      const mockProps = {
        value: 0.7,
        onChange: vi.fn(),
      };

      render(<RatingSlider {...mockProps} />);

      expect(screen.getByText('0.7')).toBeInTheDocument();
      expect(screen.getByText('(良好)')).toBeInTheDocument();
    });

    it('displays correct score level for different values', () => {
      const { rerender } = render(
        <RatingSlider value={0.9} onChange={vi.fn()} />
      );
      expect(screen.getByText('(优秀)')).toBeInTheDocument();

      rerender(<RatingSlider value={0.5} onChange={vi.fn()} />);
      expect(screen.getByText('(一般)')).toBeInTheDocument();

      rerender(<RatingSlider value={0.2} onChange={vi.fn()} />);
      expect(screen.getByText('(较差)')).toBeInTheDocument();
    });
  });

  describe('ChosenSelector', () => {
    it('renders Y/N buttons', () => {
      const mockProps = {
        chosen: false,
        onChange: vi.fn(),
      };

      render(<ChosenSelector {...mockProps} />);

      expect(screen.getByText('Y')).toBeInTheDocument();
      expect(screen.getByText('N')).toBeInTheDocument();
      expect(screen.getByText('未选择')).toBeInTheDocument();
    });

    it('shows correct state when chosen is true', () => {
      const mockProps = {
        chosen: true,
        onChange: vi.fn(),
      };

      render(<ChosenSelector {...mockProps} />);

      expect(screen.getByText('已选为最佳')).toBeInTheDocument();
    });

    it('calls onChange when buttons are clicked', () => {
      const mockOnChange = vi.fn();
      const mockProps = {
        chosen: false,
        onChange: mockOnChange,
      };

      render(<ChosenSelector {...mockProps} />);

      const yButton = screen.getByText('Y');
      const nButton = screen.getByText('N');

      fireEvent.click(yButton);
      expect(mockOnChange).toHaveBeenCalledWith(true);

      fireEvent.click(nButton);
      expect(mockOnChange).toHaveBeenCalledWith(false);
    });
  });

  describe('CandidateList', () => {
    const mockCandidates: COTCandidate[] = [
      {
        id: '1',
        text: 'Answer 1',
        chainOfThought: 'Reasoning 1',
        score: 0.8,
        chosen: true,
        rank: 1,
      },
      {
        id: '2',
        text: 'Answer 2',
        chainOfThought: 'Reasoning 2',
        score: 0.6,
        chosen: false,
        rank: 2,
      },
    ];

    it('renders candidate list with statistics', () => {
      const mockProps = {
        candidates: mockCandidates,
        onChange: vi.fn(),
      };

      render(
        <TestWrapper>
          <CandidateList {...mockProps} />
        </TestWrapper>
      );

      expect(screen.getByText('候选答案 (2)')).toBeInTheDocument();
      expect(screen.getByText('总数: 2')).toBeInTheDocument();
      expect(screen.getByText('已选择: 1')).toBeInTheDocument();
      expect(screen.getByText('平均分: 0.70')).toBeInTheDocument();
    });

    it('shows empty state when no candidates', () => {
      const mockProps = {
        candidates: [],
        onChange: vi.fn(),
      };

      render(
        <TestWrapper>
          <CandidateList {...mockProps} />
        </TestWrapper>
      );

      expect(screen.getByText('暂无候选答案')).toBeInTheDocument();
      expect(screen.getByText('添加第一个候选答案')).toBeInTheDocument();
    });

    it('adds new candidate when add button is clicked', () => {
      const mockOnChange = vi.fn();
      const mockProps = {
        candidates: [],
        onChange: mockOnChange,
      };

      render(
        <TestWrapper>
          <CandidateList {...mockProps} />
        </TestWrapper>
      );

      const addButton = screen.getByText('添加第一个候选答案');
      fireEvent.click(addButton);

      expect(mockOnChange).toHaveBeenCalledWith([
        expect.objectContaining({
          text: '',
          chainOfThought: '',
          score: 0.5,
          chosen: false,
          rank: 1,
        }),
      ]);
    });
  });

  describe('CandidateItem', () => {
    const mockCandidate: COTCandidate = {
      id: '1',
      text: 'Test answer',
      chainOfThought: 'Test reasoning',
      score: 0.7,
      chosen: false,
      rank: 1,
    };

    it('renders candidate item with all fields', () => {
      const mockProps = {
        candidate: mockCandidate,
        index: 0,
        onUpdate: vi.fn(),
        onDelete: vi.fn(),
        onMove: vi.fn(),
        onSetChosen: vi.fn(),
      };

      render(
        <TestWrapper>
          <CandidateItem {...mockProps} />
        </TestWrapper>
      );

      expect(screen.getByText('候选答案 #1')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test answer')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test reasoning')).toBeInTheDocument();
      expect(screen.getByText('0.7')).toBeInTheDocument();
    });

    it('shows chosen state correctly', () => {
      const chosenCandidate = { ...mockCandidate, chosen: true };
      const mockProps = {
        candidate: chosenCandidate,
        index: 0,
        onUpdate: vi.fn(),
        onDelete: vi.fn(),
        onMove: vi.fn(),
        onSetChosen: vi.fn(),
      };

      render(
        <TestWrapper>
          <CandidateItem {...mockProps} />
        </TestWrapper>
      );

      expect(screen.getByText('✓ 已选择')).toBeInTheDocument();
    });

    it('calls onUpdate when text fields change', () => {
      const mockOnUpdate = vi.fn();
      const mockProps = {
        candidate: mockCandidate,
        index: 0,
        onUpdate: mockOnUpdate,
        onDelete: vi.fn(),
        onMove: vi.fn(),
        onSetChosen: vi.fn(),
      };

      render(
        <TestWrapper>
          <CandidateItem {...mockProps} />
        </TestWrapper>
      );

      const textInput = screen.getByDisplayValue('Test answer');
      fireEvent.change(textInput, { target: { value: 'Updated answer' } });

      expect(mockOnUpdate).toHaveBeenCalledWith({ text: 'Updated answer' });
    });
  });

  describe('TextSelector', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('renders search input and slice list', async () => {
      const mockProps = {
        projectId: 'test-project',
        selectedSliceId: null,
        onTextSelect: vi.fn(),
        onSliceSelect: vi.fn(),
      };

      render(<TextSelector {...mockProps} />);

      expect(screen.getByPlaceholderText('搜索切片内容...')).toBeInTheDocument();
      expect(screen.getByText('点击切片选择，然后在右侧内容中拖拽选择文本')).toBeInTheDocument();
    });
  });
});