"""
数据库查询优化和索引管理
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import text, Index, inspect
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from app.core.database import engine, SessionLocal
from app.core.app_logging import logger


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        
    def create_performance_indexes(self) -> Dict[str, bool]:
        """创建性能优化索引"""
        indexes_created = {}
        
        # 定义需要创建的索引
        indexes_to_create = [
            # 项目相关索引
            ("idx_projects_owner_status", "projects", ["owner_id", "status"]),
            ("idx_projects_name_search", "projects", ["name"]),
            ("idx_projects_created_at", "projects", ["created_at"]),
            
            # 文件相关索引
            ("idx_files_project_status", "files", ["project_id", "ocr_status"]),
            ("idx_files_hash_lookup", "files", ["file_hash"]),
            ("idx_files_mime_type", "files", ["mime_type"]),
            ("idx_files_size", "files", ["size"]),
            
            # 切片相关索引
            ("idx_slices_file_type", "slices", ["file_id", "slice_type"]),
            ("idx_slices_page_number", "slices", ["page_number"]),
            
            # CoT相关索引
            ("idx_cot_items_project_status", "cot_items", ["project_id", "status"]),
            ("idx_cot_items_slice_id", "cot_items", ["slice_id"]),
            ("idx_cot_items_created_by", "cot_items", ["created_by"]),
            ("idx_cot_items_source", "cot_items", ["source"]),
            
            # CoT候选答案索引
            ("idx_cot_candidates_item_rank", "cot_candidates", ["cot_item_id", "rank"]),
            ("idx_cot_candidates_chosen", "cot_candidates", ["chosen"]),
            ("idx_cot_candidates_score", "cot_candidates", ["score"]),
            
            # 任务相关索引
            ("idx_tasks_status_priority", "tasks", ["status", "priority"]),
            ("idx_tasks_project_id", "tasks", ["project_id"]),
            ("idx_tasks_created_at", "tasks", ["created_at"]),
            
            # 审计日志索引
            ("idx_audit_logs_user_action", "audit_logs", ["user_id", "action"]),
            ("idx_audit_logs_timestamp", "audit_logs", ["timestamp"]),
            ("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"]),
        ]
        
        with self.engine.connect() as conn:
            for index_name, table_name, columns in indexes_to_create:
                try:
                    # 检查索引是否已存在
                    if not self._index_exists(conn, index_name, table_name):
                        # 创建索引
                        columns_str = ", ".join(columns)
                        create_index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
                        conn.execute(text(create_index_sql))
                        conn.commit()
                        indexes_created[index_name] = True
                        logger.info(f"Created index: {index_name}")
                    else:
                        indexes_created[index_name] = False
                        logger.info(f"Index already exists: {index_name}")
                        
                except Exception as e:
                    logger.error(f"Failed to create index {index_name}: {e}")
                    indexes_created[index_name] = False
                    
        return indexes_created
    
    def _index_exists(self, conn, index_name: str, table_name: str) -> bool:
        """检查索引是否存在"""
        try:
            # PostgreSQL查询索引
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE indexname = :index_name
            """), {"index_name": index_name})
            return result.fetchone() is not None
        except Exception:
            return False
    
    def analyze_query_performance(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """分析查询性能"""
        with self.engine.connect() as conn:
            try:
                # PostgreSQL执行EXPLAIN
                explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
                result = conn.execute(text(explain_query), params or {})
                
                execution_plan = []
                for row in result:
                    execution_plan.append(row[0])  # PostgreSQL返回JSON格式
                
                return {
                    "query": query,
                    "execution_plan": execution_plan,
                    "analysis_time": "N/A"
                }
                
            except Exception as e:
                logger.error(f"Query analysis failed: {e}")
                return {"error": str(e)}
    
    def get_table_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取表统计信息"""
        statistics = {}
        
        tables = [
            "projects", "files", "slices", "cot_items", 
            "cot_candidates", "tasks", "audit_logs", "users"
        ]
        
        with self.engine.connect() as conn:
            for table in tables:
                try:
                    # 获取行数
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = count_result.scalar()
                    
                    # PostgreSQL获取表列信息
                    table_info = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = :table_name
                    """), {"table_name": table})
                    columns = [row[0] for row in table_info]
                    
                    statistics[table] = {
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": columns
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to get statistics for table {table}: {e}")
                    statistics[table] = {"error": str(e)}
        
        return statistics
    
    def optimize_database(self) -> Dict[str, Any]:
        """执行数据库优化"""
        optimization_results = {}
        
        with self.engine.connect() as conn:
            try:
                # PostgreSQL执行VACUUM优化
                conn.execute(text("VACUUM"))
                optimization_results["vacuum"] = "completed"
                
                # PostgreSQL执行ANALYZE更新统计信息
                conn.execute(text("ANALYZE"))
                optimization_results["analyze"] = "completed"
                
                # PostgreSQL执行REINDEX
                conn.execute(text("REINDEX DATABASE cotdb"))
                optimization_results["reindex"] = "completed"
                
                conn.commit()
                logger.info("Database optimization completed")
                
            except Exception as e:
                logger.error(f"Database optimization failed: {e}")
                optimization_results["error"] = str(e)
        
        return optimization_results


# 全局数据库优化器实例
db_optimizer = DatabaseOptimizer(engine)


def init_database_optimization():
    """初始化数据库优化"""
    logger.info("Initializing database optimization...")
    
    # 创建性能索引
    indexes_created = db_optimizer.create_performance_indexes()
    logger.info(f"Database indexes created: {sum(indexes_created.values())} new indexes")
    
    # 执行初始优化
    optimization_results = db_optimizer.optimize_database()
    logger.info(f"Database optimization results: {optimization_results}")
    
    return {
        "indexes_created": indexes_created,
        "optimization_results": optimization_results
    }


def get_database_performance_stats() -> Dict[str, Any]:
    """获取数据库性能统计"""
    return {
        "table_statistics": db_optimizer.get_table_statistics(),
        "engine_info": {
            "url": str(engine.url),
            "pool_size": "N/A",
            "checked_out": "N/A"
        }
    }