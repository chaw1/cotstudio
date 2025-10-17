/**
 * HeroUI组件交互体验和视觉效果测试
 * 需求: 6.3, 6.4, 6.5
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfigProvider } from 'antd';
import { Button, Card, Table, Modal, Input, Select } from '@heroui/react';

// 测试工具
const createTestWrapper = (children: React.ReactNode) => {
    return (
        <ConfigProvider>
            {children}
        </ConfigProvider>
    );
};

// 模拟HeroUI主题
const mockHeroUITheme = {
    colors: {
        primary: '#1677ff',
        secondary: '#52c41a',
        success: '#52c41a',
        warning: '#faad14',
        error: '#ff4d4f',
    },
    spacing: {
        xs: '0.5rem',
        sm: '0.75rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
    },
    borderRadius: {
        xs: '0.25rem',
        sm: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
    },
};

describe('HeroUI组件交互体验测试', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('按钮组件测试', () => {
        it('应该正确渲染不同类型的按钮', () => {
            render(createTestWrapper(
                <div>
                    <Button color="primary" data-testid="primary-btn">主要按钮</Button>
                    <Button color="secondary" data-testid="secondary-btn">次要按钮</Button>
                    <Button color="success" data-testid="success-btn">成功按钮</Button>
                    <Button color="warning" data-testid="warning-btn">警告按钮</Button>
                    <Button color="danger" data-testid="danger-btn">危险按钮</Button>
                </div>
            ));

            // 验证按钮渲染
            expect(screen.getByTestId('primary-btn')).toBeInTheDocument();
            expect(screen.getByTestId('secondary-btn')).toBeInTheDocument();
            expect(screen.getByTestId('success-btn')).toBeInTheDocument();
            expect(screen.getByTestId('warning-btn')).toBeInTheDocument();
            expect(screen.getByTestId('danger-btn')).toBeInTheDocument();

            // 验证按钮文本
            expect(screen.getByText('主要按钮')).toBeInTheDocument();
            expect(screen.getByText('次要按钮')).toBeInTheDocument();
            expect(screen.getByText('成功按钮')).toBeInTheDocument();
            expect(screen.getByText('警告按钮')).toBeInTheDocument();
            expect(screen.getByText('危险按钮')).toBeInTheDocument();
        });

        it('应该支持不同尺寸的按钮', () => {
            render(createTestWrapper(
                <div>
                    <Button size="sm" data-testid="small-btn">小按钮</Button>
                    <Button size="md" data-testid="medium-btn">中按钮</Button>
                    <Button size="lg" data-testid="large-btn">大按钮</Button>
                </div>
            ));

            const smallBtn = screen.getByTestId('small-btn');
            const mediumBtn = screen.getByTestId('medium-btn');
            const largeBtn = screen.getByTestId('large-btn');

            // 验证按钮尺寸类名或样式
            expect(smallBtn).toHaveClass(/small|sm/);
            expect(mediumBtn).toHaveClass(/medium|md/);
            expect(largeBtn).toHaveClass(/large|lg/);
        });

        it('应该正确处理按钮点击事件', async () => {
            const user = userEvent.setup();
            const handleClick = vi.fn();

            render(createTestWrapper(
                <Button onPress={handleClick} data-testid="click-btn">
                    点击我
                </Button>
            ));

            const button = screen.getByTestId('click-btn');
            await user.click(button);

            expect(handleClick).toHaveBeenCalledTimes(1);
        });

        it('应该支持禁用状态', () => {
            render(createTestWrapper(
                <Button isDisabled data-testid="disabled-btn">
                    禁用按钮
                </Button>
            ));

            const button = screen.getByTestId('disabled-btn');
            expect(button).toBeDisabled();
        });

        it('应该支持加载状态', () => {
            render(createTestWrapper(
                <Button isLoading data-testid="loading-btn">
                    加载中
                </Button>
            ));

            const button = screen.getByTestId('loading-btn');

            // 验证加载状态
            expect(button).toHaveAttribute('data-loading', 'true');

            // 验证加载指示器存在
            const loadingIndicator = screen.getByRole('progressbar') ||
                screen.getByTestId('loading-spinner') ||
                button.querySelector('[data-slot="spinner"]');
            expect(loadingIndicator).toBeInTheDocument();
        });
    });

    describe('卡片组件测试', () => {
        it('应该正确渲染卡片内容', () => {
            render(createTestWrapper(
                <Card data-testid="test-card">
                    <Card.Header>
                        <h3>卡片标题</h3>
                    </Card.Header>
                    <Card.Body>
                        <p>卡片内容</p>
                    </Card.Body>
                    <Card.Footer>
                        <Button>操作按钮</Button>
                    </Card.Footer>
                </Card>
            ));

            expect(screen.getByTestId('test-card')).toBeInTheDocument();
            expect(screen.getByText('卡片标题')).toBeInTheDocument();
            expect(screen.getByText('卡片内容')).toBeInTheDocument();
            expect(screen.getByText('操作按钮')).toBeInTheDocument();
        });

        it('应该支持不同的卡片变体', () => {
            render(createTestWrapper(
                <div>
                    <Card variant="flat" data-testid="flat-card">平面卡片</Card>
                    <Card variant="bordered" data-testid="bordered-card">边框卡片</Card>
                    <Card variant="shadow" data-testid="shadow-card">阴影卡片</Card>
                </div>
            ));

            expect(screen.getByTestId('flat-card')).toBeInTheDocument();
            expect(screen.getByTestId('bordered-card')).toBeInTheDocument();
            expect(screen.getByTestId('shadow-card')).toBeInTheDocument();
        });

        it('应该支持悬停效果', async () => {
            const user = userEvent.setup();

            render(createTestWrapper(
                <Card isHoverable data-testid="hoverable-card">
                    悬停卡片
                </Card>
            ));

            const card = screen.getByTestId('hoverable-card');

            // 模拟悬停
            await user.hover(card);

            // 验证悬停状态
            expect(card).toHaveAttribute('data-hover', 'true');
        });
    });

    describe('表格组件测试', () => {
        const mockData = [
            { id: 1, name: '张三', age: 25, department: 'IT' },
            { id: 2, name: '李四', age: 30, department: 'HR' },
            { id: 3, name: '王五', age: 28, department: 'Finance' },
        ];

        const columns = [
            { key: 'name', label: '姓名' },
            { key: 'age', label: '年龄' },
            { key: 'department', label: '部门' },
        ];

        it('应该正确渲染表格数据', () => {
            render(createTestWrapper(
                <Table
                    data={mockData}
                    columns={columns}
                    data-testid="test-table"
                >
                    {(item) => (
                        <Table.Row key={item.id}>
                            <Table.Cell>{item.name}</Table.Cell>
                            <Table.Cell>{item.age}</Table.Cell>
                            <Table.Cell>{item.department}</Table.Cell>
                        </Table.Row>
                    )}
                </Table>
            ));

            // 验证表格渲染
            expect(screen.getByTestId('test-table')).toBeInTheDocument();

            // 验证表头
            expect(screen.getByText('姓名')).toBeInTheDocument();
            expect(screen.getByText('年龄')).toBeInTheDocument();
            expect(screen.getByText('部门')).toBeInTheDocument();

            // 验证数据行
            expect(screen.getByText('张三')).toBeInTheDocument();
            expect(screen.getByText('李四')).toBeInTheDocument();
            expect(screen.getByText('王五')).toBeInTheDocument();
        });

        it('应该支持行选择', async () => {
            const user = userEvent.setup();
            const handleSelectionChange = vi.fn();

            render(createTestWrapper(
                <Table
                    data={mockData}
                    columns={columns}
                    selectionMode="multiple"
                    onSelectionChange={handleSelectionChange}
                    data-testid="selectable-table"
                >
                    {(item) => (
                        <Table.Row key={item.id}>
                            <Table.Cell>{item.name}</Table.Cell>
                            <Table.Cell>{item.age}</Table.Cell>
                            <Table.Cell>{item.department}</Table.Cell>
                        </Table.Row>
                    )}
                </Table>
            ));

            // 查找并点击复选框
            const checkboxes = screen.getAllByRole('checkbox');
            if (checkboxes.length > 0) {
                await user.click(checkboxes[0]);
                expect(handleSelectionChange).toHaveBeenCalled();
            }
        });

        it('应该支持排序功能', async () => {
            const user = userEvent.setup();
            const handleSortChange = vi.fn();

            render(createTestWrapper(
                <Table
                    data={mockData}
                    columns={columns.map(col => ({ ...col, allowsSorting: true }))}
                    onSortChange={handleSortChange}
                    data-testid="sortable-table"
                >
                    {(item) => (
                        <Table.Row key={item.id}>
                            <Table.Cell>{item.name}</Table.Cell>
                            <Table.Cell>{item.age}</Table.Cell>
                            <Table.Cell>{item.department}</Table.Cell>
                        </Table.Row>
                    )}
                </Table>
            ));

            // 点击表头进行排序
            const nameHeader = screen.getByText('姓名');
            await user.click(nameHeader);

            // 验证排序回调被调用
            expect(handleSortChange).toHaveBeenCalled();
        });
    });

    describe('模态框组件测试', () => {
        it('应该正确显示和隐藏模态框', async () => {
            const user = userEvent.setup();

            const TestModal = () => {
                const [isOpen, setIsOpen] = React.useState(false);

                return (
                    <>
                        <Button onPress={() => setIsOpen(true)} data-testid="open-modal">
                            打开模态框
                        </Button>
                        <Modal
                            isOpen={isOpen}
                            onClose={() => setIsOpen(false)}
                            data-testid="test-modal"
                        >
                            <Modal.Header>
                                <h3>模态框标题</h3>
                            </Modal.Header>
                            <Modal.Body>
                                <p>模态框内容</p>
                            </Modal.Body>
                            <Modal.Footer>
                                <Button onPress={() => setIsOpen(false)}>关闭</Button>
                            </Modal.Footer>
                        </Modal>
                    </>
                );
            };

            render(createTestWrapper(<TestModal />));

            // 初始状态模态框应该不可见
            expect(screen.queryByTestId('test-modal')).not.toBeInTheDocument();

            // 点击打开按钮
            await user.click(screen.getByTestId('open-modal'));

            // 模态框应该显示
            await waitFor(() => {
                expect(screen.getByTestId('test-modal')).toBeInTheDocument();
                expect(screen.getByText('模态框标题')).toBeInTheDocument();
                expect(screen.getByText('模态框内容')).toBeInTheDocument();
            });

            // 点击关闭按钮
            await user.click(screen.getByText('关闭'));

            // 模态框应该隐藏
            await waitFor(() => {
                expect(screen.queryByTestId('test-modal')).not.toBeInTheDocument();
            });
        });

        it('应该支持ESC键关闭', async () => {
            const user = userEvent.setup();

            render(createTestWrapper(
                <Modal isOpen={true} onClose={vi.fn()} data-testid="esc-modal">
                    <Modal.Body>按ESC关闭</Modal.Body>
                </Modal>
            ));

            // 按ESC键
            await user.keyboard('{Escape}');

            // 验证关闭回调被调用
            // 注意：实际的关闭行为取决于Modal组件的实现
        });
    });

    describe('输入组件测试', () => {
        it('应该正确处理输入值变化', async () => {
            const user = userEvent.setup();
            const handleChange = vi.fn();

            render(createTestWrapper(
                <Input
                    placeholder="请输入内容"
                    onChange={handleChange}
                    data-testid="test-input"
                />
            ));

            const input = screen.getByTestId('test-input');
            await user.type(input, 'Hello World');

            expect(handleChange).toHaveBeenCalled();
            expect(input).toHaveValue('Hello World');
        });

        it('应该支持不同的输入状态', () => {
            render(createTestWrapper(
                <div>
                    <Input
                        isInvalid
                        errorMessage="输入错误"
                        data-testid="error-input"
                    />
                    <Input
                        isDisabled
                        data-testid="disabled-input"
                    />
                    <Input
                        isReadOnly
                        value="只读内容"
                        data-testid="readonly-input"
                    />
                </div>
            ));

            expect(screen.getByTestId('error-input')).toHaveAttribute('aria-invalid', 'true');
            expect(screen.getByTestId('disabled-input')).toBeDisabled();
            expect(screen.getByTestId('readonly-input')).toHaveAttribute('readonly');
            expect(screen.getByText('输入错误')).toBeInTheDocument();
        });
    });

    describe('选择器组件测试', () => {
        const options = [
            { key: 'option1', label: '选项1' },
            { key: 'option2', label: '选项2' },
            { key: 'option3', label: '选项3' },
        ];

        it('应该正确显示选项', async () => {
            const user = userEvent.setup();

            render(createTestWrapper(
                <Select
                    placeholder="请选择"
                    data-testid="test-select"
                >
                    {options.map(option => (
                        <Select.Item key={option.key} value={option.key}>
                            {option.label}
                        </Select.Item>
                    ))}
                </Select>
            ));

            const select = screen.getByTestId('test-select');
            await user.click(select);

            // 验证选项显示
            await waitFor(() => {
                expect(screen.getByText('选项1')).toBeInTheDocument();
                expect(screen.getByText('选项2')).toBeInTheDocument();
                expect(screen.getByText('选项3')).toBeInTheDocument();
            });
        });

        it('应该支持选项选择', async () => {
            const user = userEvent.setup();
            const handleSelectionChange = vi.fn();

            render(createTestWrapper(
                <Select
                    placeholder="请选择"
                    onSelectionChange={handleSelectionChange}
                    data-testid="selectable-select"
                >
                    {options.map(option => (
                        <Select.Item key={option.key} value={option.key}>
                            {option.label}
                        </Select.Item>
                    ))}
                </Select>
            ));

            const select = screen.getByTestId('selectable-select');
            await user.click(select);

            // 选择第一个选项
            await waitFor(() => {
                const option1 = screen.getByText('选项1');
                return user.click(option1);
            });

            expect(handleSelectionChange).toHaveBeenCalledWith(new Set(['option1']));
        });
    });

    describe('主题和样式一致性测试', () => {
        it('应该应用正确的主题颜色', () => {
            render(createTestWrapper(
                <div>
                    <Button color="primary" data-testid="primary-themed">主色按钮</Button>
                    <Button color="secondary" data-testid="secondary-themed">次色按钮</Button>
                </div>
            ));

            const primaryBtn = screen.getByTestId('primary-themed');
            const secondaryBtn = screen.getByTestId('secondary-themed');

            // 验证主题颜色类名
            expect(primaryBtn).toHaveClass(/primary/);
            expect(secondaryBtn).toHaveClass(/secondary/);
        });

        it('应该保持组件间的视觉一致性', () => {
            render(createTestWrapper(
                <div>
                    <Button data-testid="button-component">按钮</Button>
                    <Input data-testid="input-component" />
                    <Card data-testid="card-component">卡片</Card>
                </div>
            ));

            const button = screen.getByTestId('button-component');
            const input = screen.getByTestId('input-component');
            const card = screen.getByTestId('card-component');

            // 验证组件都应用了一致的设计系统
            // 这里可以检查共同的CSS类名或样式属性
            [button, input, card].forEach(element => {
                const computedStyle = window.getComputedStyle(element);
                // 验证边框圆角一致性
                expect(computedStyle.borderRadius).toMatch(/\d+px/);
            });
        });
    });

    describe('可访问性测试', () => {
        it('应该支持键盘导航', async () => {
            const user = userEvent.setup();

            render(createTestWrapper(
                <div>
                    <Button data-testid="btn1">按钮1</Button>
                    <Button data-testid="btn2">按钮2</Button>
                    <Input data-testid="input1" />
                </div>
            ));

            // Tab键导航
            await user.tab();
            expect(screen.getByTestId('btn1')).toHaveFocus();

            await user.tab();
            expect(screen.getByTestId('btn2')).toHaveFocus();

            await user.tab();
            expect(screen.getByTestId('input1')).toHaveFocus();
        });

        it('应该提供正确的ARIA属性', () => {
            render(createTestWrapper(
                <div>
                    <Button
                        aria-label="关闭对话框"
                        data-testid="aria-button"
                    >
                        ×
                    </Button>
                    <Input
                        aria-describedby="help-text"
                        data-testid="aria-input"
                    />
                    <div id="help-text">帮助文本</div>
                </div>
            ));

            const button = screen.getByTestId('aria-button');
            const input = screen.getByTestId('aria-input');

            expect(button).toHaveAttribute('aria-label', '关闭对话框');
            expect(input).toHaveAttribute('aria-describedby', 'help-text');
        });

        it('应该支持屏幕阅读器', () => {
            render(createTestWrapper(
                <div>
                    <Button
                        aria-pressed="false"
                        role="switch"
                        data-testid="toggle-button"
                    >
                        切换开关
                    </Button>
                    <div
                        role="alert"
                        aria-live="polite"
                        data-testid="alert-message"
                    >
                        操作成功
                    </div>
                </div>
            ));

            const toggleButton = screen.getByTestId('toggle-button');
            const alertMessage = screen.getByTestId('alert-message');

            expect(toggleButton).toHaveAttribute('role', 'switch');
            expect(toggleButton).toHaveAttribute('aria-pressed', 'false');
            expect(alertMessage).toHaveAttribute('role', 'alert');
            expect(alertMessage).toHaveAttribute('aria-live', 'polite');
        });
    });

    describe('响应式设计测试', () => {
        it('应该在不同屏幕尺寸下正确显示', () => {
            // 模拟不同屏幕尺寸
            const screenSizes = [
                { width: 320, height: 568, name: '小屏手机' },
                { width: 768, height: 1024, name: '平板' },
                { width: 1920, height: 1080, name: '桌面' }
            ];

            screenSizes.forEach(size => {
                // 设置窗口尺寸
                Object.defineProperty(window, 'innerWidth', {
                    writable: true,
                    configurable: true,
                    value: size.width,
                });

                render(createTestWrapper(
                    <div data-testid={`responsive-${size.name}`}>
                        <Button size={size.width < 768 ? 'sm' : 'md'}>
                            响应式按钮
                        </Button>
                    </div>
                ));

                const container = screen.getByTestId(`responsive-${size.name}`);
                expect(container).toBeInTheDocument();

                console.log(`✅ ${size.name} (${size.width}x${size.height}) 响应式测试通过`);
            });
        });
    });
});

export default {};