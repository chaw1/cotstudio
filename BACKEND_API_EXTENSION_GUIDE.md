# 后端API扩展 - 用户贡献统计增强

## 概述

为了支持前端Dashboard中用户贡献部分的新增统计信息（文件数量和知识图谱数量），需要对后端API进行相应的扩展。

## API端点修改

### 端点: `/analytics/user-contributions`

**当前返回结构**:
```json
{
  "success": true,
  "data": {
    "users": [...],
    "datasets": [...],
    "relationships": [...],
    "summary": {
      "total_users": 5,
      "total_projects": 12,
      "total_relationships": 25,
      "total_cot_items": 348
    }
  }
}
```

**需要扩展的返回结构**:
```json
{
  "success": true,
  "data": {
    "users": [...],
    "datasets": [...],
    "relationships": [...],
    "summary": {
      "total_users": 5,
      "total_projects": 12,
      "total_relationships": 25,
      "total_cot_items": 348,
      "total_files": 156,           // 新增：总文件数量
      "total_knowledge_graphs": 8   // 新增：总知识图谱数量
    }
  }
}
```

## 数据计算逻辑

### 文件数量统计 (total_files)

建议实现方式：

```python
# 方式1：基于项目文件关联表统计
def get_total_files():
    """统计所有项目的文件总数"""
    return db.query(func.count(ProjectFile.id)).scalar()

# 方式2：基于文件上传记录统计
def get_total_files():
    """统计所有已上传的文件数量"""
    return db.query(func.count(UploadedFile.id)).filter(
        UploadedFile.status == 'active',
        UploadedFile.deleted_at.is_(None)
    ).scalar()

# 方式3：基于项目聚合统计
def get_total_files():
    """基于项目中的文件计数统计"""
    return db.query(func.sum(Project.file_count)).scalar() or 0
```

### 知识图谱数量统计 (total_knowledge_graphs)

建议实现方式：

```python
# 方式1：基于知识图谱表直接统计
def get_total_knowledge_graphs():
    """统计所有知识图谱数量"""
    return db.query(func.count(KnowledgeGraph.id)).filter(
        KnowledgeGraph.status == 'active',
        KnowledgeGraph.deleted_at.is_(None)
    ).scalar()

# 方式2：基于项目知识图谱关联统计
def get_total_knowledge_graphs():
    """统计有知识图谱的项目数量"""
    return db.query(func.count(distinct(ProjectKnowledgeGraph.project_id))).scalar()

# 方式3：基于Neo4j图数据库统计
async def get_total_knowledge_graphs():
    """从Neo4j统计知识图谱数量"""
    async with driver.session() as session:
        result = await session.run("MATCH (n:Graph) RETURN count(n) as count")
        record = await result.single()
        return record["count"] if record else 0
```

## 后端实现建议

### 1. 修改数据模型 (如果需要)

```python
# app/models/analytics.py
class ContributionSummary(BaseModel):
    total_users: int
    total_projects: int
    total_relationships: int
    total_cot_items: int
    total_files: int = 0              # 新增字段
    total_knowledge_graphs: int = 0   # 新增字段
```

### 2. 修改服务层

```python
# app/services/analytics_service.py
class AnalyticsService:
    def get_user_contributions(self, db: Session) -> dict:
        # ... 现有逻辑 ...
        
        # 计算新的统计数据
        total_files = self._calculate_total_files(db)
        total_knowledge_graphs = self._calculate_total_knowledge_graphs(db)
        
        summary = {
            "total_users": len(users),
            "total_projects": len(projects),
            "total_relationships": len(relationships),
            "total_cot_items": sum(user.get('total_cot_items', 0) for user in users),
            "total_files": total_files,
            "total_knowledge_graphs": total_knowledge_graphs
        }
        
        return {
            "users": users,
            "datasets": projects,
            "relationships": relationships,
            "summary": summary
        }
    
    def _calculate_total_files(self, db: Session) -> int:
        """计算总文件数量"""
        # 实现文件统计逻辑
        return db.query(func.count(File.id)).filter(
            File.deleted_at.is_(None)
        ).scalar() or 0
    
    def _calculate_total_knowledge_graphs(self, db: Session) -> int:
        """计算总知识图谱数量"""
        # 实现知识图谱统计逻辑
        return db.query(func.count(KnowledgeGraph.id)).filter(
            KnowledgeGraph.status == 'active'
        ).scalar() or 0
```

### 3. 修改API控制器

```python
# app/api/v1/endpoints/analytics.py
@router.get("/user-contributions")
async def get_user_contributions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户贡献数据（包含新的统计信息）"""
    analytics_service = AnalyticsService()
    data = analytics_service.get_user_contributions(db)
    
    return APIResponse.success(data=data)
```

## 数据库优化建议

### 1. 添加索引

```sql
-- 为文件统计添加索引
CREATE INDEX idx_files_status_deleted ON files(status, deleted_at);

-- 为知识图谱统计添加索引
CREATE INDEX idx_knowledge_graphs_status ON knowledge_graphs(status);

-- 为项目文件关联添加索引
CREATE INDEX idx_project_files_project_id ON project_files(project_id);
```

### 2. 考虑缓存

```python
# 使用Redis缓存统计数据
@cache(expire=300)  # 缓存5分钟
def get_contribution_statistics():
    """获取贡献统计数据（带缓存）"""
    # ... 统计逻辑 ...
```

## 前端适配

### 已完成的前端修改

✅ **接口类型定义**: 已扩展 `ContributionData` 接口，添加了 `total_files` 和 `total_knowledge_graphs` 字段

✅ **UI显示**: 已在统计信息栏添加文件数量和知识图谱数量的显示

✅ **图标和样式**: 已添加合适的图标和颜色配置：
- 文件数量：使用 `FolderOutlined` 图标，橙色 (#fa8c16)
- 知识图谱数量：使用 `ShareAltOutlined` 图标，青色 (#13c2c2)

✅ **数据容错**: 已添加默认值处理和基于现有数据的估算逻辑

✅ **响应式设计**: 已优化移动设备上的显示效果

### 当前的估算逻辑

在后端实现新字段之前，前端使用以下估算逻辑：

```typescript
// 文件数量估算：基于项目数据或平均每个项目2.5个文件
total_files = result.data.datasets?.reduce((sum, project) => 
  sum + (project.file_count || 0), 0) || 
  Math.floor(result.data.summary.total_projects * 2.5)

// 知识图谱数量估算：假设80%的项目有知识图谱
total_knowledge_graphs = Math.floor(result.data.summary.total_projects * 0.8)
```

## 测试建议

### 1. 单元测试

```python
def test_get_user_contributions_with_new_fields():
    """测试用户贡献API返回新字段"""
    response = client.get("/api/v1/analytics/user-contributions")
    data = response.json()["data"]
    
    assert "total_files" in data["summary"]
    assert "total_knowledge_graphs" in data["summary"]
    assert isinstance(data["summary"]["total_files"], int)
    assert isinstance(data["summary"]["total_knowledge_graphs"], int)
```

### 2. 集成测试

```python
def test_contribution_statistics_accuracy():
    """测试统计数据的准确性"""
    # 创建测试数据
    # 验证统计结果
    # 确保计算逻辑正确
```

## 实施优先级

1. **高优先级**: 实现基础的文件和知识图谱统计
2. **中优先级**: 添加缓存和性能优化
3. **低优先级**: 实现复杂的聚合统计和实时更新

## 注意事项

1. **性能考虑**: 统计查询可能比较耗时，建议使用缓存
2. **数据一致性**: 确保统计数据与实际数据保持一致
3. **错误处理**: 统计失败时应有合适的默认值
4. **权限控制**: 确保统计数据的访问权限正确

这个扩展将为用户提供更全面的贡献数据视图，提升Dashboard的信息价值。