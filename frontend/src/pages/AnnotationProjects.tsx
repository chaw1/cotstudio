import React, { useState, useEffect } from 'react';
import { Card, List, Button, Typography, Space, Tag, Empty, Spin } from 'antd';
import { ProjectOutlined, FileTextOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { projectService } from '../services/projectService';
import { Project } from '../types';

const { Title, Text } = Typography;

const AnnotationProjects: React.FC = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadProjects();
    }, []);

    const loadProjects = async () => {
        try {
            setLoading(true);
            const projectList = await projectService.getProjects();
            setProjects(projectList);
        } catch (error) {
            console.error('Failed to load projects:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleProjectSelect = (projectId: string) => {
        navigate(`/annotation/${projectId}`);
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'green';
            case 'completed': return 'blue';
            case 'paused': return 'orange';
            default: return 'default';
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case 'active': return '活跃';
            case 'completed': return '已完成';
            case 'paused': return '暂停';
            default: return status;
        }
    };

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '400px'
            }}>
                <Spin size="large" />
            </div>
        );
    }

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ marginBottom: '24px' }}>
                <Title level={2} style={{ margin: 0, color: '#262626' }}>
                    CoT 标注项目
                </Title>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                    选择一个项目开始 Chain-of-Thought 标注工作
                </Text>
            </div>

            {projects.length === 0 ? (
                <Card>
                    <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description={
                            <div>
                                <Text type="secondary">暂无可用项目</Text>
                                <br />
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    请先创建项目并上传文件后再进行标注
                                </Text>
                            </div>
                        }
                    >
                        <Button
                            type="primary"
                            onClick={() => navigate('/projects')}
                            icon={<ProjectOutlined />}
                        >
                            创建项目
                        </Button>
                    </Empty>
                </Card>
            ) : (
                <List
                    grid={{
                        gutter: 16,
                        xs: 1,
                        sm: 2,
                        md: 2,
                        lg: 3,
                        xl: 3,
                        xxl: 4,
                    }}
                    dataSource={projects}
                    renderItem={(project) => (
                        <List.Item>
                            <Card
                                hoverable
                                className="modern-card"
                                actions={[
                                    <Button
                                        type="primary"
                                        icon={<ArrowRightOutlined />}
                                        onClick={() => handleProjectSelect(project.id)}
                                    >
                                        开始标注
                                    </Button>
                                ]}
                            >
                                <Card.Meta
                                    avatar={
                                        <div style={{
                                            width: '48px',
                                            height: '48px',
                                            background: 'linear-gradient(135deg, #1677ff 0%, #69c0ff 100%)',
                                            borderRadius: '12px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontSize: '20px'
                                        }}>
                                            <FileTextOutlined />
                                        </div>
                                    }
                                    title={
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span>{project.name}</span>
                                            <Tag color={getStatusColor(project.status)}>
                                                {getStatusText(project.status)}
                                            </Tag>
                                        </div>
                                    }
                                    description={
                                        <div>
                                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                                {project.description || '暂无描述'}
                                            </Text>
                                            <div style={{ marginTop: '12px' }}>
                                                <Space size="large">
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>文件数</Text>
                                                        <br />
                                                        <Text strong>{project.fileCount || 0}</Text>
                                                    </div>
                                                    <div>
                                                        <Text type="secondary" style={{ fontSize: '12px' }}>CoT数据</Text>
                                                        <br />
                                                        <Text strong>{project.cotCount || 0}</Text>
                                                    </div>
                                                </Space>
                                            </div>
                                        </div>
                                    }
                                />
                            </Card>
                        </List.Item>
                    )}
                />
            )}
        </div>
    );
};

export default AnnotationProjects;