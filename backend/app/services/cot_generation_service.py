"""
CoT生成服务
基于选定文本片段生成Chain-of-Thought问题和候选答案
"""
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from .llm_service import LLMService, LLMMessage, LLMError
from ..core.config import settings
from ..models.slice import Slice
from ..schemas.cot import COTCreate, COTCandidateCreate


logger = logging.getLogger(__name__)


class COTGenerationService:
    """CoT生成服务类"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        
        # DeepSeek专用的系统提示词
        self.question_generation_prompt = """你是一个专业的学术研究助手，擅长基于给定文本生成高质量的Chain-of-Thought (CoT)问题。

请根据以下文本片段，生成一个需要深度思考和推理的学术级别问题。问题应该：
1. 需要多步推理才能回答
2. 具有学术价值和深度
3. 能够引导出清晰的思维链条
4. 适合进行CoT格式的回答

请直接返回问题，不要包含其他解释。问题长度控制在100字以内。"""

        self.answer_generation_prompt = """你是一个专业的学术研究助手，擅长生成高质量的Chain-of-Thought (CoT)格式答案。

请基于给定的问题和文本片段，生成{candidate_count}个不同的CoT格式答案。每个答案都应该：
1. 包含清晰的思维步骤
2. 逻辑推理过程完整
3. 结论明确且有依据
4. 风格和角度略有不同

请按以下JSON格式返回：
{{
    "candidates": [
        {{
            "text": "最终答案内容",
            "chain_of_thought": "详细的思维推理过程，包含步骤1、步骤2等"
        }},
        ...
    ]
}}

确保返回有效的JSON格式，每个答案都有完整的思维链条。"""
    
    async def generate_question(self, slice_content: str, context: Optional[str] = None) -> str:
        """
        基于文本片段生成CoT问题
        
        Args:
            slice_content: 文本片段内容
            context: 可选的上下文信息
            
        Returns:
            生成的问题文本
        """
        try:
            # 构建用户消息
            user_content = f"文本片段：\n{slice_content}"
            if context:
                user_content += f"\n\n上下文：\n{context}"
            
            messages = [
                LLMMessage(role="system", content=self.question_generation_prompt),
                LLMMessage(role="user", content=user_content)
            ]
            
            # 调用DeepSeek生成问题
            response = await self.llm_service.generate_completion(
                messages=messages,
                provider="deepseek",
                temperature=0.8,
                max_tokens=200
            )
            
            question = response.content.strip()
            
            # 验证问题长度
            if len(question) > settings.COT_QUESTION_MAX_LENGTH:
                question = question[:settings.COT_QUESTION_MAX_LENGTH].rsplit(' ', 1)[0] + "..."
            
            logger.info(f"Generated question for slice content (length: {len(slice_content)})")
            return question
            
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            raise LLMError(f"Failed to generate question: {str(e)}", provider="deepseek")
    
    async def generate_candidates(
        self, 
        question: str, 
        slice_content: str, 
        candidate_count: Optional[int] = None,
        context: Optional[str] = None
    ) -> List[COTCandidateCreate]:
        """
        生成CoT候选答案
        
        Args:
            question: 问题文本
            slice_content: 文本片段内容
            candidate_count: 候选答案数量
            context: 可选的上下文信息
            
        Returns:
            候选答案列表
        """
        try:
            # 确定候选答案数量
            if candidate_count is None:
                candidate_count = settings.COT_CANDIDATE_COUNT
            
            candidate_count = max(
                settings.COT_MIN_CANDIDATE_COUNT,
                min(candidate_count, settings.COT_MAX_CANDIDATE_COUNT)
            )
            
            # 构建用户消息
            user_content = f"问题：{question}\n\n文本片段：\n{slice_content}"
            if context:
                user_content += f"\n\n上下文：\n{context}"
            
            messages = [
                LLMMessage(
                    role="system", 
                    content=self.answer_generation_prompt.format(candidate_count=candidate_count)
                ),
                LLMMessage(role="user", content=user_content)
            ]
            
            # 调用DeepSeek生成候选答案
            response = await self.llm_service.generate_completion(
                messages=messages,
                provider="deepseek",
                temperature=0.9,
                max_tokens=1500
            )
            
            # 解析JSON响应
            try:
                response_data = json.loads(response.content)
                candidates_data = response_data.get("candidates", [])
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试提取候选答案
                logger.warning("Failed to parse JSON response, attempting to extract candidates")
                candidates_data = self._extract_candidates_from_text(response.content, candidate_count)
            
            # 转换为COTCandidateCreate对象
            candidates = []
            for i, candidate_data in enumerate(candidates_data[:candidate_count]):
                if isinstance(candidate_data, dict):
                    text = candidate_data.get("text", "").strip()
                    chain_of_thought = candidate_data.get("chain_of_thought", "").strip()
                else:
                    # 如果不是字典格式，尝试作为文本处理
                    text = str(candidate_data).strip()
                    chain_of_thought = ""
                
                # 验证答案长度
                if len(text) > settings.COT_ANSWER_MAX_LENGTH:
                    text = text[:settings.COT_ANSWER_MAX_LENGTH].rsplit(' ', 1)[0] + "..."
                
                if len(chain_of_thought) > settings.COT_ANSWER_MAX_LENGTH:
                    chain_of_thought = chain_of_thought[:settings.COT_ANSWER_MAX_LENGTH].rsplit(' ', 1)[0] + "..."
                
                if text:  # 只添加非空答案
                    candidates.append(COTCandidateCreate(
                        text=text,
                        chain_of_thought=chain_of_thought,
                        score=0.0,  # 初始分数为0
                        chosen=False,  # 初始都不选中
                        rank=i + 1  # 排序从1开始
                    ))
            
            # 确保至少有最小数量的候选答案
            if len(candidates) < settings.COT_MIN_CANDIDATE_COUNT:
                logger.warning(f"Generated only {len(candidates)} candidates, expected at least {settings.COT_MIN_CANDIDATE_COUNT}")
                # 可以在这里添加重试逻辑或生成默认答案
            
            logger.info(f"Generated {len(candidates)} candidates for question")
            return candidates
            
        except Exception as e:
            logger.error(f"Error generating candidates: {str(e)}")
            raise LLMError(f"Failed to generate candidates: {str(e)}", provider="deepseek")
    
    def _extract_candidates_from_text(self, text: str, expected_count: int) -> List[Dict[str, str]]:
        """
        从文本中提取候选答案（当JSON解析失败时的备用方法）
        
        Args:
            text: 响应文本
            expected_count: 期望的候选答案数量
            
        Returns:
            候选答案列表
        """
        candidates = []
        
        # 尝试按行分割并查找答案模式
        lines = text.split('\n')
        current_candidate = {"text": "", "chain_of_thought": ""}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是新的候选答案开始
            if any(marker in line.lower() for marker in ["答案", "candidate", "回答", "解答"]):
                if current_candidate["text"]:
                    candidates.append(current_candidate.copy())
                    current_candidate = {"text": "", "chain_of_thought": ""}
            
            # 检查是否是思维过程
            if any(marker in line.lower() for marker in ["思维", "推理", "分析", "步骤", "chain"]):
                current_candidate["chain_of_thought"] += line + " "
            else:
                current_candidate["text"] += line + " "
        
        # 添加最后一个候选答案
        if current_candidate["text"]:
            candidates.append(current_candidate)
        
        # 如果仍然没有足够的候选答案，创建默认答案
        while len(candidates) < expected_count:
            candidates.append({
                "text": f"基于给定文本的分析答案 {len(candidates) + 1}",
                "chain_of_thought": "需要进一步分析和推理"
            })
        
        return candidates[:expected_count]
    
    async def generate_cot_item(
        self,
        project_id: UUID,
        slice_id: UUID,
        slice_content: str,
        created_by: str,
        candidate_count: Optional[int] = None,
        context: Optional[str] = None
    ) -> COTCreate:
        """
        生成完整的CoT数据项
        
        Args:
            project_id: 项目ID
            slice_id: 切片ID
            slice_content: 文本片段内容
            created_by: 创建者
            candidate_count: 候选答案数量
            context: 可选的上下文信息
            
        Returns:
            完整的CoT创建数据
        """
        try:
            # 生成问题
            question = await self.generate_question(slice_content, context)
            
            # 生成候选答案
            candidates = await self.generate_candidates(
                question=question,
                slice_content=slice_content,
                candidate_count=candidate_count,
                context=context
            )
            
            # 创建LLM元数据
            llm_metadata = {
                "provider": "deepseek",
                "model": settings.DEEPSEEK_MODEL,
                "question_generation": {
                    "temperature": 0.8,
                    "max_tokens": 200
                },
                "answer_generation": {
                    "temperature": 0.9,
                    "max_tokens": 1500,
                    "candidate_count": len(candidates)
                },
                "slice_content_length": len(slice_content),
                "context_provided": context is not None
            }
            
            # 创建CoT数据项
            cot_create = COTCreate(
                project_id=project_id,
                slice_id=slice_id,
                question=question,
                candidates=candidates,
                llm_metadata=llm_metadata
            )
            
            logger.info(f"Generated complete CoT item for slice {slice_id}")
            return cot_create
            
        except Exception as e:
            logger.error(f"Error generating CoT item: {str(e)}")
            raise LLMError(f"Failed to generate CoT item: {str(e)}", provider="deepseek")
    
    async def regenerate_question(self, cot_item_id: UUID, slice_content: str, context: Optional[str] = None) -> str:
        """
        重新生成问题
        
        Args:
            cot_item_id: CoT项目ID
            slice_content: 文本片段内容
            context: 可选的上下文信息
            
        Returns:
            新生成的问题
        """
        return await self.generate_question(slice_content, context)
    
    async def regenerate_candidates(
        self,
        question: str,
        slice_content: str,
        candidate_count: Optional[int] = None,
        context: Optional[str] = None
    ) -> List[COTCandidateCreate]:
        """
        重新生成候选答案
        
        Args:
            question: 问题文本
            slice_content: 文本片段内容
            candidate_count: 候选答案数量
            context: 可选的上下文信息
            
        Returns:
            新生成的候选答案列表
        """
        return await self.generate_candidates(question, slice_content, candidate_count, context)


# 创建全局CoT生成服务实例
def create_cot_generation_service() -> COTGenerationService:
    """创建CoT生成服务实例"""
    from .llm_service import llm_service
    return COTGenerationService(llm_service)