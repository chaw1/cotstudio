"""
WebSocket端点用于实时通信
"""
import json
from datetime import datetime
from typing import Dict, List, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from uuid import UUID

from app.core.app_logging import logger
from app.middleware.auth import get_current_user

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.task_subscriptions: Dict[str, Set[str]] = {}  # task_id -> set of user_ids
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> set of task_ids
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """连接WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        logger.info("WebSocket connected", user_id=user_id)
        
        # 发送连接确认
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """断开WebSocket连接"""
        
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # 清理订阅
                if user_id in self.user_subscriptions:
                    for task_id in self.user_subscriptions[user_id]:
                        if task_id in self.task_subscriptions:
                            self.task_subscriptions[task_id].discard(user_id)
                            if not self.task_subscriptions[task_id]:
                                del self.task_subscriptions[task_id]
                    del self.user_subscriptions[user_id]
        
        logger.info("WebSocket disconnected", user_id=user_id)
    
    async def send_personal_message(self, message: dict, user_id: str):
        """发送个人消息"""
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error("Failed to send WebSocket message", user_id=user_id, error=str(e))
                    disconnected_connections.append(connection)
            
            # 清理断开的连接
            for connection in disconnected_connections:
                self.disconnect(connection, user_id)
    
    async def send_task_update(self, task_id: str, user_id: str, status: str, progress: int = None, message: str = None, data: Optional[Dict] = None):
        """发送任务更新"""
        update = {
            "type": "task_update",
            "task_id": task_id,
            "user_id": user_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        await self.send_personal_message(update, user_id)
        
        # 同时发送给订阅了该任务的其他用户
        if task_id in self.task_subscriptions:
            for subscribed_user_id in self.task_subscriptions[task_id]:
                if subscribed_user_id != user_id:
                    await self.send_personal_message(update, subscribed_user_id)
    
    async def subscribe_to_task(self, user_id: str, task_id: str):
        """订阅任务更新"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(user_id)
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(task_id)
        
        logger.info("User subscribed to task", user_id=user_id, task_id=task_id)
    
    async def unsubscribe_from_task(self, user_id: str, task_id: str):
        """取消订阅任务更新"""
        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(user_id)
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]
        
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(task_id)
        
        logger.info("User unsubscribed from task", user_id=user_id, task_id=task_id)
    
    async def broadcast_task_event(self, task_id: str, event_type: str, data: Optional[Dict] = None):
        """广播任务事件给所有订阅者"""
        if task_id in self.task_subscriptions:
            message = {
                "type": event_type,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data or {}
            }
            
            for user_id in self.task_subscriptions[task_id]:
                await self.send_personal_message(message, user_id)
    
    def get_active_users(self) -> List[str]:
        """获取活跃用户列表"""
        return list(self.active_connections.keys())
    
    def get_user_task_subscriptions(self, user_id: str) -> List[str]:
        """获取用户订阅的任务列表"""
        return list(self.user_subscriptions.get(user_id, set()))


# 全局连接管理器实例
manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket端点 - 支持任务监控和实时通信
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                # 处理不同类型的消息
                if message_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message_type == "subscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.subscribe_to_task(user_id, task_id)
                        await websocket.send_text(json.dumps({
                            "type": "subscription_confirmed",
                            "task_id": task_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Missing task_id in subscribe_task message"
                        }))
                
                elif message_type == "unsubscribe_task":
                    task_id = message.get("task_id")
                    if task_id:
                        await manager.unsubscribe_from_task(user_id, task_id)
                        await websocket.send_text(json.dumps({
                            "type": "unsubscription_confirmed",
                            "task_id": task_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                
                elif message_type == "get_subscriptions":
                    subscriptions = manager.get_user_task_subscriptions(user_id)
                    await websocket.send_text(json.dumps({
                        "type": "subscriptions_list",
                        "task_ids": subscriptions,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message_type == "heartbeat":
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat_ack",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error("Error processing WebSocket message", user_id=user_id, error=str(e))
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("WebSocket error", user_id=user_id, error=str(e))
        manager.disconnect(websocket, user_id)


# 导出连接管理器供其他模块使用
__all__ = ["manager", "router"]