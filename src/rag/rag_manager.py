"""
RAG 知识库管理器

使用 ChromaDB + Ollama 实现 RAG（检索增强生成）

Issue: #34 RAG-001
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaEmbeddingFunction:
    """
    Ollama 嵌入函数（适配 ChromaDB 接口）
    """
    
    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ImportError("请安装 ollama: pip install ollama")
    
    def name(self) -> str:
        """返回嵌入函数名称（ChromaDB 要求）"""
        return f"ollama_{self.model_name}"
    
    def embed_query(self, input: List[str]) -> List[List[float]]:
        """ChromaDB 查询嵌入接口"""
        return self(input)
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """生成嵌入向量"""
        embeddings = []
        for text in input:
            try:
                response = self.ollama.embeddings(
                    model=self.model_name,
                    prompt=text
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                logger.warning(f"Ollama 嵌入失败: {e}，使用备用嵌入")
                # 备用：简单哈希嵌入
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                hash_int = int(hash_obj.hexdigest(), 16)
                embedding = [float((hash_int >> (i % 64)) & 1) for i in range(768)]
                embeddings.append(embedding)
        return embeddings


class RAGManager:
    """
    RAG 知识库管理器
    
    使用 ChromaDB 作为向量数据库，Ollama 作为嵌入模型。
    
    使用方法：
        manager = RAGManager()
        manager.load_knowledge_base()
        results = manager.search("价值投资原则", top_k=5)
    """
    
    def __init__(
        self,
        knowledge_base_dir: str = "knowledge_base",
        persist_dir: str = ".chromadb",
        collection_name: str = "alpha_knowledge",
        embedding_model: str = "nomic-embed-text"
    ):
        """
        初始化 RAG 管理器
        
        Args:
            knowledge_base_dir: 知识库文件目录
            persist_dir: ChromaDB 持久化目录
            collection_name: 集合名称
            embedding_model: Ollama 嵌入模型名称
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = None
        
        logger.info(f"RAG 管理器初始化: {knowledge_base_dir}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        使用 Ollama 获取文本嵌入
        
        Args:
            text: 输入文本
        
        Returns:
            嵌入向量
        """
        try:
            import ollama
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            logger.warning(f"Ollama 嵌入失败: {e}，使用简单哈希嵌入")
            # 回退：使用简单的哈希嵌入
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            # 生成 768 维向量
            embedding = []
            for i in range(768):
                val = (hash_int >> (i % 64)) & 1
                embedding.append(float(val))
            return embedding
    
    def load_knowledge_base(self) -> int:
        """
        加载知识库文件到 ChromaDB
        
        Returns:
            加载的文档数量
        """
        logger.info("开始加载知识库...")
        
        # 创建 Ollama 嵌入函数
        try:
            embedding_func = OllamaEmbeddingFunction(self.embedding_model)
            logger.info(f"使用 Ollama 嵌入模型: {self.embedding_model}")
        except Exception as e:
            logger.warning(f"Ollama 嵌入初始化失败: {e}，使用默认嵌入")
            embedding_func = None
        
        # 创建或获取集合
        if embedding_func:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_func,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        # 遍历知识库目录
        documents = []
        metadatas = []
        ids = []
        
        for file_path in self.knowledge_base_dir.glob("*.md"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分段（按段落）
            paragraphs = content.split('\n\n')
            
            for i, para in enumerate(paragraphs):
                if para.strip():
                    doc_id = f"{file_path.stem}_{i}"
                    documents.append(para.strip())
                    metadatas.append({
                        "source": file_path.name,
                        "chunk_index": i
                    })
                    ids.append(doc_id)
        
        if documents:
            # 添加到集合
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"已加载 {len(documents)} 个文档片段")
        
        return len(documents)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
        
        Returns:
            搜索结果列表
        """
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        # 执行搜索
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter_metadata
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000
    ) -> str:
        """
        为查询获取上下文
        
        Args:
            query: 查询文本
            max_tokens: 最大 token 数
        
        Returns:
            上下文文本
        """
        results = self.search(query, top_k=5)
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 2  # 粗略估计
        
        for result in results:
            doc = result['document']
            if total_chars + len(doc) > max_chars:
                break
            context_parts.append(doc)
            total_chars += len(doc)
        
        return "\n\n".join(context_parts)
    
    def clear_collection(self):
        """清空集合"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"已清空集合: {self.collection_name}")
        except Exception as e:
            logger.warning(f"清空集合失败: {e}")


# 便捷函数
def get_rag_manager() -> RAGManager:
    """获取 RAG 管理器实例"""
    return RAGManager()


def search_knowledge(query: str, top_k: int = 5) -> List[Dict]:
    """搜索知识库（便捷函数）"""
    manager = RAGManager()
    return manager.search(query, top_k)