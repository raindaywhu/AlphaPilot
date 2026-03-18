/**
 * AlphaPilot Web UI JavaScript
 * 
 * 处理用户交互和 API 调用
 */

// API 基础 URL
const API_BASE_URL = '/api';

// 常见股票映射（本地搜索建议）
const POPULAR_STOCKS = {
    "贵州茅台": "sh600519",
    "五粮液": "sz000858",
    "宁德时代": "sz300750",
    "比亚迪": "sz002594",
    "招商银行": "sh600036",
    "中国平安": "sh601318",
    "工商银行": "sh601398",
    "恒瑞医药": "sh600276",
    "美的集团": "sz000333",
    "隆基绿能": "sh601012",
    "中国石油": "sh601857",
    "中国石化": "sh600028",
    "中国移动": "sh600941",
    "伊利股份": "sh600887",
    "海天味业": "sh603288"
};

// DOM 元素
const stockCodeInput = document.getElementById('stockCode');
const suggestionsDiv = document.getElementById('suggestions');
const timeHorizonInput = document.getElementById('timeHorizon');
const parallelModeCheckbox = document.getElementById('parallelMode');
const analyzeBtn = document.getElementById('analyzeBtn');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

// 事件监听
document.addEventListener('DOMContentLoaded', () => {
    // 分析按钮点击
    analyzeBtn.addEventListener('click', handleAnalyze);
    
    // 回车键触发分析
    stockCodeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleAnalyze();
        }
    });
    
    // 搜索建议
    stockCodeInput.addEventListener('input', handleSearchSuggestions);
    
    // 点击外部关闭建议
    document.addEventListener('click', (e) => {
        if (!stockCodeInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });
});

/**
 * 处理搜索建议
 */
function handleSearchSuggestions() {
    const query = stockCodeInput.value.trim().toLowerCase();
    
    if (query.length < 1) {
        suggestionsDiv.style.display = 'none';
        return;
    }
    
    const matches = [];
    
    // 搜索本地股票库
    for (const [name, code] of Object.entries(POPULAR_STOCKS)) {
        if (name.toLowerCase().includes(query) || code.toLowerCase().includes(query)) {
            matches.push({ name, code });
        }
        if (matches.length >= 5) break;
    }
    
    if (matches.length === 0) {
        suggestionsDiv.style.display = 'none';
        return;
    }
    
    // 显示建议
    suggestionsDiv.innerHTML = matches.map(item => `
        <div class="suggestion-item" onclick="selectSuggestion('${item.code}', '${item.name}')">
            <span class="suggestion-name">${item.name}</span>
            <span class="suggestion-code">${item.code}</span>
        </div>
    `).join('');
    
    suggestionsDiv.style.display = 'block';
}

/**
 * 选择建议
 */
function selectSuggestion(code, name) {
    stockCodeInput.value = name;
    suggestionsDiv.style.display = 'none';
    // 自动触发分析
    handleAnalyze();
}

/**
 * 处理分析请求
 */
async function handleAnalyze() {
    const stockCode = stockCodeInput.value.trim().toUpperCase();
    
    // 验证输入
    if (!stockCode) {
        showError('请输入股票代码');
        return;
    }
    
    // 格式化股票代码（添加 SH/SZ 前缀）
    const formattedCode = formatStockCode(stockCode);
    
    // 获取参数
    const timeHorizon = parseInt(timeHorizonInput.value) || 5;
    const parallel = parallelModeCheckbox.checked;
    
    // 显示加载状态
    setLoading(true);
    hideError();
    
    try {
        // 调用 API
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                stock_code: formattedCode,
                time_horizon: timeHorizon,
                parallel: parallel
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '分析失败');
        }
        
        const data = await response.json();
        
        // 显示结果
        displayResults(data);
        
    } catch (error) {
        console.error('分析错误:', error);
        showError(error.message || '分析失败，请稍后重试');
    } finally {
        setLoading(false);
    }
}

/**
 * 格式化股票代码
 * 添加 SH 或 SZ 前缀（仅对纯数字代码）
 */
function formatStockCode(code) {
    // 中文名称直接返回（API 会处理）
    if (/[\u4e00-\u9fa5]/.test(code)) {
        return code;
    }
    
    // 已经有前缀
    if (code.toLowerCase().startsWith('sh') || code.toLowerCase().startsWith('sz')) {
        return code.toUpperCase();
    }
    
    // 纯数字代码，添加前缀
    const codeNum = code.replace(/[^0-9]/g, '');
    if (!codeNum) {
        return code;
    }
    
    // 6 开头为上海，0/3 开头为深圳
    if (codeNum.startsWith('6')) {
        return `SH${codeNum}`;
    } else if (codeNum.startsWith('0') || codeNum.startsWith('3')) {
        return `SZ${codeNum}`;
    }
    
    return code;
}

/**
 * 显示分析结果
 */
function displayResults(data) {
    // 显示结果区域
    resultSection.style.display = 'block';
    
    // 股票代码
    document.getElementById('stockCodeDisplay').textContent = data.stock_code;
    
    // 综合评级
    const ratingElement = document.getElementById('overallRating');
    const rating = data.overall_rating || '中性';
    ratingElement.textContent = rating;
    ratingElement.className = 'rating-value ' + getRatingClass(rating);
    
    // 置信度
    const confidence = (data.confidence * 100).toFixed(1);
    document.getElementById('confidence').textContent = `${confidence}%`;
    
    // 得分
    const score = (data.score * 100).toFixed(1);
    document.getElementById('score').textContent = `${score}分`;
    
    // 分析日期
    document.getElementById('analysisDate').textContent = data.analysis_date;
    
    // Agent 结果
    displayAgentResult('quantitativeResult', data.quantitative);
    displayAgentResult('macroResult', data.macro);
    displayAgentResult('alternativeResult', data.alternative);
    
    // 投资建议
    document.getElementById('summary').innerHTML = formatText(data.summary || '暂无投资建议');
    
    // 风险提示
    const riskSection = document.getElementById('riskSection');
    const riskWarnings = document.getElementById('riskWarnings');
    
    if (data.risk_warnings && data.risk_warnings.length > 0) {
        riskSection.style.display = 'block';
        riskWarnings.innerHTML = data.risk_warnings
            .map(warning => `<li>${warning}</li>`)
            .join('');
    } else {
        riskSection.style.display = 'none';
    }
    
    // 执行时间
    document.getElementById('executionTime').textContent = data.execution_time || '未知';
    
    // 滚动到结果
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * 显示 Agent 结果
 */
function displayAgentResult(elementId, result) {
    const element = document.getElementById(elementId);
    
    if (!result || Object.keys(result).length === 0) {
        element.innerHTML = '<p class="loading-text">暂无分析结果</p>';
        return;
    }
    
    let html = '';
    
    // 评级
    if (result.rating) {
        html += `<p><span class="label">评级:</span> <span class="content">${result.rating}</span></p>`;
    }
    
    // 置信度
    if (result.confidence !== undefined) {
        html += `<p><span class="label">置信度:</span> <span class="content">${(result.confidence * 100).toFixed(1)}%</span></p>`;
    }
    
    // 分析内容
    if (result.analysis) {
        html += `<p><span class="label">分析:</span> <span class="content">${formatText(result.analysis)}</span></p>`;
    }
    
    // 建议
    if (result.recommendation) {
        html += `<p><span class="label">建议:</span> <span class="content">${result.recommendation}</span></p>`;
    }
    
    // 其他字段
    const excludeKeys = ['rating', 'confidence', 'analysis', 'recommendation'];
    for (const [key, value] of Object.entries(result)) {
        if (!excludeKeys.includes(key) && value !== null && value !== undefined) {
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const displayValue = typeof value === 'object' ? JSON.stringify(value) : value;
            html += `<p><span class="label">${label}:</span> <span class="content">${displayValue}</span></p>`;
        }
    }
    
    element.innerHTML = html || '<p class="loading-text">暂无分析结果</p>';
}

/**
 * 获取评级样式类
 */
function getRatingClass(rating) {
    const ratingMap = {
        '看涨': 'bullish',
        '中性偏多': 'bullish-leaning',
        '中性': 'neutral',
        '中性偏空': 'bearish-leaning',
        '看跌': 'bearish'
    };
    
    // 支持英文
    const englishMap = {
        'bullish': 'bullish',
        'bullish-leaning': 'bullish-leaning',
        'neutral': 'neutral',
        'bearish-leaning': 'bearish-leaning',
        'bearish': 'bearish'
    };
    
    return ratingMap[rating] || englishMap[rating.toLowerCase()] || 'neutral';
}

/**
 * 格式化文本（处理换行等）
 */
function formatText(text) {
    if (!text) return '';
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

/**
 * 设置加载状态
 */
function setLoading(loading) {
    const btnText = analyzeBtn.querySelector('.btn-text');
    const btnLoading = analyzeBtn.querySelector('.btn-loading');
    
    if (loading) {
        analyzeBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
    } else {
        analyzeBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

/**
 * 显示错误
 */
function showError(message) {
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
    resultSection.style.display = 'none';
}

/**
 * 隐藏错误
 */
function hideError() {
    errorSection.style.display = 'none';
}