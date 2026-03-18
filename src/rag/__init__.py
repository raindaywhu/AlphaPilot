"""
RAG 模块

检索增强生成（Retrieval-Augmented Generation）
"""

from .rag_manager import RAGManager, get_rag_manager, search_knowledge

__all__ = [
    'RAGManager',
    'get_rag_manager',
    'search_knowledge'
]