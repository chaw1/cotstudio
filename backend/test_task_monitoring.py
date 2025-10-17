"""
任务监控系统测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.models.task import TaskMonitor, TaskStatus, TaskType, TaskPriority
from app.schemas.task import TaskMonitorCreate, TaskMonitorUpdate, TaskFilterParams
from app.services.task_monitor_service import task_monitor_service
from app.api.v1.websocket import ConnectionManager


class TestTaskMonitorModel:
    """测试任务监控模型"""
    
    def test_task_monitor_creation(self):
        """测试任务监控记录创建"""
        task_monitor = TaskMonitor(
            task_id="test-task-123",
            task_name="test_task",
            task_type=TaskType.OCR_PROCESSING,
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            user_id="user123",
            queue_name="default"
        )
        
        assert task_monitor.task_id == "test-task-123"
        assert task_monitor.task_type == TaskType.OCR_PROCESSING
        assert task_monitor.status == TaskStatus.PENDING
        assert task_monitor.is_active == True
        assert task_monitor.is_completed == False
        assert task_monitor.can_retry() == False
    
    def test_execution_time_calculation(self):
        """测试执行时间计算"""
        now = datetime.utcnow()
        task_monitor = TaskMonitor(
            task_id="test-task-123",
            task_name="test_task",
            task_type=TaskType.OCR_PROCESSING,
            status=TaskStatus.SUCCESS,
            priority=TaskPriority.NORMAL,
            user_id="user123",
            queue_name="default",
            started_at=now - timedelta(minutes=5),
            completed_at=now
        )
        
        execution_time = task_monitor.execution_time
        assert execution_time == 300  # 5 minutes = 300 seconds
    
    def test_can_retry_logic(self):
        """测试重试逻辑"""
        task_monitor = TaskMonitor(
            task_id="test-task-123",
            task_name="test_task",
            task_type=TaskType.OCR_PROCESSING,
            status=TaskStatus.FAILURE,
            priority=TaskPriority.NORMAL,
            user_id="user123",
            queue_name="default",
            retry_count=1,
            max_retries=3
        )
        
        assert task_monitor.can_retry() == True
        
        # 达到最大重试次数
        task_monitor.retry_count = 3
        assert task_monitor.can_retry() == False
        
        # 成功状态不能重试
        task_monitor.status = TaskStatus.SUCCESS
        task_monitor.retry_count = 1
        assert task_monitor.can_retry() == False


class TestTaskMonitorService:
    """测试任务监控服务"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    def test_create_task_monitor(self, mock_db):
        """测试创建任务监控记录"""
        task_data = TaskMonitorCreate(
            task_id="test-task-123",
            task_name="test_task",
            task_type=TaskType.OCR_PROCESSING,
            user_id="user123"
        )
        
        mock_task = Mock(spec=TaskMonitor)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.models.task.TaskMonitor', return_value=mock_task):
            result = task_monitor_service.create_task_monitor(mock_db, task_data)
            
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
    
    def test_update_task_monitor(self, mock_db):
        """测试更新任务监控记录"""
        task_id = "test-task-123"
        update_data = TaskMonitorUpdate(
            status=TaskStatus.PROGRESS,
            progress=50,
            message="Processing..."
        )
        
        mock_task = Mock(spec=TaskMonitor)
        mock_task.started_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        
        result = task_monitor_service.update_task_monitor(mock_db, task_id, update_data)
        
        assert mock_task.status == TaskStatus.PROGRESS
        assert mock_task.progress == 50
        assert mock_task.message == "Processing..."
        mock_db.commit.assert_called_once()
    
    def test_list_task_monitors_with_filters(self, mock_db):
        """测试带过滤条件的任务列表查询"""
        filters = TaskFilterParams(
            status=[TaskStatus.PENDING, TaskStatus.PROGRESS],
            task_type=[TaskType.OCR_PROCESSING],
            user_id="user123",
            limit=10,
            offset=0
        )
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [Mock(spec=TaskMonitor) for _ in range(5)]
        
        tasks, total = task_monitor_service.list_task_monitors(mock_db, filters)
        
        assert len(tasks) == 5
        assert total == 5
    
    def test_retry_task(self, mock_db):
        """测试重试任务"""
        task_id = "test-task-123"
        
        mock_task = Mock(spec=TaskMonitor)
        mock_task.can_retry.return_value = True
        mock_task.retry_count = 1
        mock_task.retry_delay = 60
        mock_task.task_name = "test_task"
        mock_task.parameters = {"args": [], "kwargs": {}}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        
        with patch('app.core.celery_app.celery_app') as mock_celery:
            result = task_monitor_service.retry_task(mock_db, task_id, "Manual retry")
            
            assert result == True
            assert mock_task.retry_count == 2
            assert mock_task.status == TaskStatus.RETRY
            mock_celery.send_task.assert_called_once()
    
    def test_cancel_task(self, mock_db):
        """测试取消任务"""
        task_id = "test-task-123"
        
        mock_task = Mock(spec=TaskMonitor)
        mock_task.started_at = datetime.utcnow() - timedelta(minutes=5)
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        
        with patch('app.core.celery_app.celery_app') as mock_celery:
            result = task_monitor_service.cancel_task(mock_db, task_id, "Manual cancellation")
            
            assert result == True
            assert mock_task.status == TaskStatus.REVOKED
            assert mock_task.completed_at is not None
            mock_celery.control.revoke.assert_called_once_with(task_id, terminate=True)


class TestWebSocketManager:
    """测试WebSocket连接管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建连接管理器实例"""
        return ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, manager):
        """测试WebSocket连接"""
        mock_websocket = AsyncMock()
        user_id = "user123"
        
        await manager.connect(mock_websocket, user_id)
        
        assert user_id in manager.active_connections
        assert mock_websocket in manager.active_connections[user_id]
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_subscription(self, manager):
        """测试任务订阅"""
        user_id = "user123"
        task_id = "task123"
        
        await manager.subscribe_to_task(user_id, task_id)
        
        assert task_id in manager.task_subscriptions
        assert user_id in manager.task_subscriptions[task_id]
        assert task_id in manager.user_subscriptions[user_id]
    
    @pytest.mark.asyncio
    async def test_task_update_broadcast(self, manager):
        """测试任务更新广播"""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        user1 = "user1"
        user2 = "user2"
        task_id = "task123"
        
        # 连接两个用户
        await manager.connect(mock_websocket1, user1)
        await manager.connect(mock_websocket2, user2)
        
        # 订阅任务
        await manager.subscribe_to_task(user1, task_id)
        await manager.subscribe_to_task(user2, task_id)
        
        # 发送任务更新
        await manager.send_task_update(task_id, user1, "PROGRESS", 50, "Processing...")
        
        # 验证两个用户都收到了更新
        mock_websocket1.send_text.assert_called()
        mock_websocket2.send_text.assert_called()
    
    def test_disconnect_cleanup(self, manager):
        """测试断开连接时的清理"""
        mock_websocket = Mock()
        user_id = "user123"
        task_id = "task123"
        
        # 模拟连接和订阅
        manager.active_connections[user_id] = [mock_websocket]
        manager.user_subscriptions[user_id] = {task_id}
        manager.task_subscriptions[task_id] = {user_id}
        
        # 断开连接
        manager.disconnect(mock_websocket, user_id)
        
        # 验证清理
        assert user_id not in manager.active_connections
        assert user_id not in manager.user_subscriptions
        assert task_id not in manager.task_subscriptions


class TestTaskAPI:
    """测试任务API端点"""
    
    @pytest.fixture
    def mock_current_user(self):
        """模拟当前用户"""
        return {"user_id": "user123", "is_admin": False}
    
    @pytest.mark.asyncio
    async def test_get_tasks_endpoint(self, mock_current_user):
        """测试获取任务列表端点"""
        from app.api.v1.tasks import list_tasks
        
        mock_db = Mock(spec=Session)
        
        with patch('app.services.task_monitor_service.task_monitor_service') as mock_service:
            mock_service.list_task_monitors.return_value = ([], 0)
            
            result = await list_tasks(
                status=None,
                task_type=None,
                priority=None,
                user_id=None,
                queue_name=None,
                is_critical=None,
                limit=50,
                offset=0,
                order_by="created_at",
                order_desc=True,
                db=mock_db,
                current_user=mock_current_user
            )
            
            assert "items" in result
            assert "total" in result
            mock_service.list_task_monitors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_task_endpoint(self, mock_current_user):
        """测试重试任务端点"""
        from app.api.v1.tasks import retry_task
        from app.schemas.task import TaskRetryRequest
        
        mock_db = Mock(spec=Session)
        task_id = "test-task-123"
        retry_request = TaskRetryRequest(task_id=task_id, reason="Manual retry")
        
        mock_task = Mock()
        mock_task.user_id = "user123"
        
        with patch('app.services.task_monitor_service.task_monitor_service') as mock_service:
            mock_service.get_task_monitor.return_value = mock_task
            mock_service.retry_task.return_value = True
            
            result = await retry_task(task_id, retry_request, mock_db, mock_current_user)
            
            assert result["message"] == "Task retry initiated"
            assert result["task_id"] == task_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])