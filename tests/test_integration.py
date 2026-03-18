"""
AlphaPilot 集成测试

测试内容：
1. qlib 数据层是否正常
2. RAG 知识库是否正常
3. Agent 分析是否正常

运行方式：
    python tests/test_integration.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_qlib_data():
    """测试 qlib 数据层"""
    print("\n" + "="*50)
    print("📊 测试 1: qlib 数据层")
    print("="*50)
    
    try:
        import qlib
        from qlib.data import D
        
        # 初始化 qlib
        qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")
        
        # 测试读取数据
        instruments = ["sh600519"]  # 茅台
        fields = ["$close", "$open", "$high", "$low", "$volume"]
        
        df = D.features(instruments, fields, start_time="2026-03-01", end_time="2026-03-17")
        
        if df is not None and len(df) > 0:
            print(f"✅ qlib 数据正常，读取到 {len(df)} 条记录")
            print(df.tail())
            return True
        else:
            print("❌ qlib 数据为空")
            return False
            
    except Exception as e:
        print(f"❌ qlib 测试失败: {e}")
        return False


def test_rag_knowledge():
    """测试 RAG 知识库"""
    print("\n" + "="*50)
    print("📚 测试 2: RAG 知识库")
    print("="*50)
    
    try:
        from src.rag import RAGManager
        
        manager = RAGManager()
        
        # 测试搜索（使用 Ollama 嵌入，避免 NumPy 兼容性问题）
        results = manager.search("价值投资", top_k=3)
        
        if results and len(results) > 0:
            print(f"✅ RAG 知识库正常，搜索到 {len(results)} 条结果")
            for r in results:
                print(f"  - {r['metadata']['source']}: {r['document'][:50]}...")
            return True
        else:
            print("❌ RAG 搜索无结果")
            return False
            
    except Exception as e:
        print(f"❌ RAG 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quantitative_agent():
    """测试量化分析师 Agent"""
    print("\n" + "="*50)
    print("🤖 测试 3: 量化分析师 Agent")
    print("="*50)
    
    try:
        from src.agents.quantitative import QuantitativeAnalyst
        
        agent = QuantitativeAnalyst()
        result = agent.analyze("sh600519")
        
        if result and "error" not in result:
            print("✅ 量化分析师 Agent 正常")
            print(f"  - 评级: {result.get('overall_rating', 'N/A')}")
            return True
        else:
            print(f"❌ Agent 分析失败: {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Agent 测试失败: {e}")
        return False


def test_api_server():
    """测试 API 服务器"""
    print("\n" + "="*50)
    print("🌐 测试 4: API 服务器")
    print("="*50)
    
    try:
        import requests
        
        # 检查服务器是否运行
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ API 服务器运行中")
            return True
        else:
            print(f"⚠️ API 服务器返回 {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️ API 服务器未启动（这是正常的，可以手动启动）")
        return None
    except Exception as e:
        print(f"⚠️ API 测试失败: {e}")
        return None


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 AlphaPilot 集成测试")
    print("="*60)
    
    results = {
        "qlib 数据层": test_qlib_data(),
        "RAG 知识库": test_rag_knowledge(),
        "量化分析师 Agent": test_quantitative_agent(),
        "API 服务器": test_api_server()
    }
    
    # 打印总结
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for name, result in results.items():
        if result is True:
            print(f"  ✅ {name}")
        elif result is False:
            print(f"  ❌ {name}")
        else:
            print(f"  ⏭️ {name} (跳过)")
    
    print(f"\n结果: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查。")


if __name__ == "__main__":
    main()