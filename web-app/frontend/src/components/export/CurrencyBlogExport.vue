<template>
  <div class="currency-blog-export">
    <div class="export-header">
      <h2>📝 外貨対応ブログエクスポート</h2>
      <p>外貨・為替レート情報を含む月次レポートをブログ投稿用に最適化して出力します</p>
    </div>
    
    <div class="export-options">
      <!-- 期間選択 -->
      <div class="option-group">
        <h3>📅 対象期間</h3>
        <div class="date-inputs">
          <input 
            type="month" 
            v-model="selectedMonth"
            class="date-input"
          >
          <button @click="setCurrentMonth" class="current-month-btn">
            今月を選択
          </button>
        </div>
      </div>
      
      <!-- 出力形式 -->
      <div class="option-group">
        <h3>📄 出力形式</h3>
        <div class="format-buttons">
          <button 
            v-for="format in exportFormats"
            :key="format.id"
            @click="selectedFormat = format.id"
            :class="['format-button', { active: selectedFormat === format.id }]"
          >
            {{ format.icon }} {{ format.name }}
          </button>
        </div>
      </div>
      
      <!-- 含める要素 -->
      <div class="option-group">
        <h3>📊 含める要素</h3>
        <div class="element-checkboxes">
          <label v-for="element in blogElements" :key="element.id" class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="element.included"
              class="checkbox-input"
            >
            <span class="checkbox-custom"></span>
            {{ element.icon }} {{ element.name }}
          </label>
        </div>
      </div>
      
      <!-- 通貨設定 -->
      <div class="option-group">
        <h3>💱 通貨表示設定</h3>
        <div class="currency-settings">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="showOriginalCurrency"
              class="checkbox-input"
            >
            <span class="checkbox-custom"></span>
            🌏 外国株の元通貨も表示
          </label>
          
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="showExchangeRateImpact"
              class="checkbox-input"
            >
            <span class="checkbox-custom"></span>
            📈 為替レート影響の分析を含める
          </label>
          
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="showCurrencyBreakdown"
              class="checkbox-input"
            >
            <span class="checkbox-custom"></span>
            🥧 通貨別構成比を表示
          </label>
        </div>
      </div>
      
      <!-- 画像設定 -->
      <div class="option-group">
        <h3>🖼️ 画像設定</h3>
        <div class="image-settings">
          <div class="setting-row">
            <label>画像品質</label>
            <select v-model="imageQuality" class="setting-select">
              <option value="0.6">低 (高速)</option>
              <option value="0.8">中 (バランス)</option>
              <option value="0.9">高 (高品質)</option>
              <option value="1.0">最高 (原寸)</option>
            </select>
          </div>
          
          <div class="setting-row">
            <label>チャートテーマ</label>
            <select v-model="chartTheme" class="setting-select">
              <option value="light">ライト</option>
              <option value="dark">ダーク</option>
              <option value="colorful">カラフル</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    
    <!-- エクスポートボタン -->
    <div class="export-actions">
      <button 
        @click="generatePreview" 
        class="preview-btn"
        :disabled="loading"
      >
        👁️ プレビュー生成
      </button>
      
      <button 
        @click="exportToBlog" 
        class="export-btn"
        :disabled="loading || !hasData"
      >
        📤 ブログ用エクスポート
      </button>
      
      <button 
        @click="downloadAsFile" 
        class="download-btn"
        :disabled="loading || !hasData"
      >
        💾 ファイルダウンロード
      </button>
    </div>
    
    <!-- プレビュー表示 -->
    <div class="preview-section" v-if="previewContent">
      <div class="preview-header">
        <h3>👁️ プレビュー</h3>
        <div class="preview-actions">
          <button @click="copyToClipboard" class="copy-btn">
            📋 クリップボードにコピー
          </button>
          <button @click="clearPreview" class="clear-btn">
            🗑️ クリア
          </button>
        </div>
      </div>
      
      <div class="preview-content" v-html="previewContent"></div>
    </div>
    
    <!-- ローディング・エラー表示 -->
    <div v-if="loading" class="loading">
      ⏳ ブログコンテンツを生成中...
    </div>
    
    <div v-if="error" class="error">
      ❌ {{ error }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'CurrencyBlogExport',
  setup() {
    const selectedMonth = ref(new Date().toISOString().slice(0, 7))
    const selectedFormat = ref('markdown')
    const loading = ref(false)
    const error = ref('')
    const previewContent = ref('')
    const portfolioData = ref([])
    const currencyData = ref([])
    const exchangeRateData = ref([])
    
    // オプション設定
    const showOriginalCurrency = ref(true)
    const showExchangeRateImpact = ref(true)
    const showCurrencyBreakdown = ref(true)
    const imageQuality = ref('0.8')
    const chartTheme = ref('light')
    
    // 出力形式
    const exportFormats = ref([
      { id: 'markdown', name: 'Markdown', icon: '📝' },
      { id: 'html', name: 'HTML', icon: '🌐' },
      { id: 'wordpress', name: 'WordPress', icon: '📄' },
      { id: 'notion', name: 'Notion', icon: '📋' }
    ])
    
    // ブログ要素
    const blogElements = ref([
      { id: 'summary', name: 'ポートフォリオ概要', icon: '📊', included: true },
      { id: 'currency_pie', name: '通貨別構成円グラフ', icon: '🥧', included: true },
      { id: 'exchange_chart', name: '為替レート推移', icon: '📈', included: true },
      { id: 'foreign_stocks', name: '外国株詳細', icon: '🌏', included: true },
      { id: 'currency_impact', name: '為替影響分析', icon: '💱', included: true },
      { id: 'performance', name: '損益レポート', icon: '💰', included: true },
      { id: 'regional_breakdown', name: '地域別分析', icon: '🗺️', included: false }
    ])
    
    // データ有無
    const hasData = computed(() => {
      return portfolioData.value.length > 0
    })
    
    // 現在月設定
    const setCurrentMonth = () => {
      selectedMonth.value = new Date().toISOString().slice(0, 7)
    }
    
    // データ取得
    const fetchData = async () => {
      try {
        loading.value = true
        
        // ポートフォリオデータ取得
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const portfolioResponse = await fetch(`${baseUrl}/api/v1/portfolio/`)
        const portfolioResult = await portfolioResponse.json()
        if (portfolioResult.error) throw new Error(portfolioResult.error)
        portfolioData.value = portfolioResult.data
        
        // 通貨サマリー取得
        const currencyResponse = await fetch('/api/currency_summary/')
        const currencyResult = await currencyResponse.json()
        if (currencyResult.error) throw new Error(currencyResult.error)
        currencyData.value = currencyResult.data
        
        // 為替レート取得
        const exchangeResponse = await fetch('/api/currency_rates/')
        const exchangeResult = await exchangeResponse.json()
        if (exchangeResult.error) {
          console.warn('為替レートデータ取得失敗:', exchangeResult.error)
        } else {
          exchangeRateData.value = exchangeResult.data
        }
        
      } catch (err) {
        error.value = `データ取得エラー: ${err.message}`
        console.error('Data fetch error:', err)
      } finally {
        loading.value = false
      }
    }
    
    // プレビュー生成
    const generatePreview = async () => {
      try {
        loading.value = true
        error.value = ''
        
        const content = await generateBlogContent()
        previewContent.value = content
        
      } catch (err) {
        error.value = `プレビュー生成エラー: ${err.message}`
        console.error('Preview generation error:', err)
      } finally {
        loading.value = false
      }
    }
    
    // ブログコンテンツ生成
    const generateBlogContent = async () => {
      const date = new Date(selectedMonth.value + '-01')
      const monthName = date.toLocaleDateString('ja-JP', { year: 'numeric', month: 'long' })
      
      let content = ''
      
      if (selectedFormat.value === 'markdown') {
        content = generateMarkdownContent(monthName)
      } else if (selectedFormat.value === 'html') {
        content = generateHTMLContent(monthName)
      } else if (selectedFormat.value === 'wordpress') {
        content = generateWordPressContent(monthName)
      } else if (selectedFormat.value === 'notion') {
        content = generateNotionContent(monthName)
      }
      
      return content
    }
    
    // Markdownコンテンツ生成
    const generateMarkdownContent = (monthName) => {
      let content = `# ${monthName} ポートフォリオレポート\n\n`
      
      if (blogElements.value.find(e => e.id === 'summary' && e.included)) {
        content += generateSummarySection()
      }
      
      if (blogElements.value.find(e => e.id === 'currency_pie' && e.included)) {
        content += generateCurrencyBreakdownSection()
      }
      
      if (blogElements.value.find(e => e.id === 'foreign_stocks' && e.included)) {
        content += generateForeignStocksSection()
      }
      
      if (blogElements.value.find(e => e.id === 'currency_impact' && e.included) && showExchangeRateImpact.value) {
        content += generateCurrencyImpactSection()
      }
      
      if (blogElements.value.find(e => e.id === 'performance' && e.included)) {
        content += generatePerformanceSection()
      }
      
      content += '\n---\n\n'
      content += '*このレポートは自動生成されました。*\n'
      content += `*生成日時: ${new Date().toLocaleString('ja-JP')}*\n`
      
      return content
    }
    
    // サマリーセクション生成
    const generateSummarySection = () => {
      const totalValue = currencyData.value.reduce((sum, currency) => sum + currency.total_cost, 0)
      const foreignStocks = portfolioData.value.filter(stock => stock.is_foreign)
      const domesticStocks = portfolioData.value.filter(stock => !stock.is_foreign)
      
      return `## 📊 ポートフォリオ概要

**総評価額**: ${formatCurrency(totalValue)}円

**構成銘柄数**: ${portfolioData.value.length}銘柄
- 🇯🇵 国内株: ${domesticStocks.length}銘柄
- 🌏 外国株: ${foreignStocks.length}銘柄

**通貨別構成**:
${currencyData.value.map(currency => 
  `- ${currency.currency}: ${formatCurrency(currency.total_cost)}円 (${currency.percentage.toFixed(1)}%)`
).join('\n')}

`
    }
    
    // 通貨別構成セクション生成
    const generateCurrencyBreakdownSection = () => {
      let content = `## 🥧 通貨別ポートフォリオ構成

`
      
      if (showCurrencyBreakdown.value) {
        content += '| 通貨 | 投資額 | 構成比 | 銘柄数 |\n'
        content += '|------|--------|--------|--------|\n'
        
        currencyData.value.forEach(currency => {
          const flag = currency.currency === 'JPY' ? '🇯🇵' : '🌏'
          content += `| ${flag} ${currency.currency} | ${formatCurrency(currency.total_cost)}円 | ${currency.percentage.toFixed(1)}% | ${currency.stocks_count}銘柄 |\n`
        })
        
        content += '\n'
      }
      
      return content
    }
    
    // 外国株セクション生成
    const generateForeignStocksSection = () => {
      const foreignStocks = portfolioData.value.filter(stock => stock.is_foreign)
      
      if (foreignStocks.length === 0) {
        return ''
      }
      
      let content = `## 🌏 外国株ホールディング

**外国株銘柄**: ${foreignStocks.length}銘柄

| 銘柄名 | ティッカー | 通貨 | 取得価格 | 保有株数 | 投資額 |\n`
      content += '|--------|------------|------|----------|----------|--------|\n'
      
      foreignStocks.forEach(stock => {
        const originalPrice = showOriginalCurrency.value ? 
          ` (${stock.purchase_price} ${stock.currency})` : ''
        const investmentAmount = stock.purchase_price * stock.shares
        
        content += `| ${stock.name} | ${stock.symbol} | ${stock.currency} | ${formatCurrency(stock.purchase_price)}円${originalPrice} | ${stock.shares}株 | ${formatCurrency(investmentAmount)}円 |\n`
      })
      
      content += '\n'
      return content
    }
    
    // 為替影響セクション生成
    const generateCurrencyImpactSection = () => {
      const foreignCurrencies = [...new Set(portfolioData.value
        .filter(stock => stock.is_foreign)
        .map(stock => stock.currency))]
      
      if (foreignCurrencies.length === 0) {
        return ''
      }
      
      let content = `## 💱 為替レート影響分析

**監視対象通貨**: ${foreignCurrencies.join(', ')}

`
      
      if (exchangeRateData.value.length > 0) {
        const latestRates = {}
        exchangeRateData.value.forEach(rate => {
          const currency = rate.currency_pair.replace('/JPY', '')
          if (foreignCurrencies.includes(currency)) {
            latestRates[currency] = rate.rate
          }
        })
        
        content += '**現在の為替レート**:\n'
        Object.entries(latestRates).forEach(([currency, rate]) => {
          content += `- ${currency}/JPY: ${rate.toFixed(2)}円\n`
        })
        content += '\n'
      }
      
      return content
    }
    
    // パフォーマンスセクション生成
    const generatePerformanceSection = () => {
      return `## 💰 今月のパフォーマンス

*詳細な損益データは別途収集予定*

**注目ポイント**:
- 外貨建て資産の為替レート変動影響
- 地域別リスク分散状況
- 通貨別パフォーマンス比較

`
    }
    
    // HTMLコンテンツ生成
    const generateHTMLContent = (monthName) => {
      const markdownContent = generateMarkdownContent(monthName)
      // 簡易的なMarkdown→HTML変換
      return `<div class="portfolio-report">
${markdownContent
  .replace(/# (.*)/g, '<h1>$1</h1>')
  .replace(/## (.*)/g, '<h2>$1</h2>')
  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  .replace(/\*(.*?)\*/g, '<em>$1</em>')
  .replace(/\n\n/g, '</p><p>')
  .replace(/\n/g, '<br>')}
</div>`
    }
    
    // 数値フォーマット
    const formatCurrency = (value) => {
      if (typeof value !== 'number') return '0'
      return new Intl.NumberFormat('ja-JP').format(Math.round(value))
    }
    
    // ブログエクスポート
    const exportToBlog = async () => {
      try {
        const content = await generateBlogContent()
        // ここで実際のブログ投稿API呼び出し
        console.log('Blog export content:', content)
        alert('ブログエクスポートが完了しました！')
      } catch (err) {
        error.value = `エクスポートエラー: ${err.message}`
      }
    }
    
    // ファイルダウンロード
    const downloadAsFile = async () => {
      try {
        const content = await generateBlogContent()
        const filename = `portfolio-report-${selectedMonth.value}.${selectedFormat.value === 'markdown' ? 'md' : 'html'}`
        
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        link.click()
        URL.revokeObjectURL(url)
      } catch (err) {
        error.value = `ダウンロードエラー: ${err.message}`
      }
    }
    
    // クリップボードにコピー
    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(previewContent.value.replace(/<[^>]*>/g, ''))
        alert('クリップボードにコピーしました！')
      } catch (err) {
        console.error('Copy failed:', err)
        alert('コピーに失敗しました')
      }
    }
    
    // プレビュークリア
    const clearPreview = () => {
      previewContent.value = ''
    }
    
    onMounted(() => {
      fetchData()
    })
    
    return {
      selectedMonth,
      selectedFormat,
      loading,
      error,
      previewContent,
      showOriginalCurrency,
      showExchangeRateImpact,
      showCurrencyBreakdown,
      imageQuality,
      chartTheme,
      exportFormats,
      blogElements,
      hasData,
      setCurrentMonth,
      generatePreview,
      exportToBlog,
      downloadAsFile,
      copyToClipboard,
      clearPreview
    }
  }
}
</script>

<style scoped>
.currency-blog-export {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.export-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.export-header h2 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 28px;
}

.export-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.export-options {
  display: grid;
  gap: 25px;
  margin-bottom: 30px;
}

.option-group {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.option-group h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
}

.date-inputs {
  display: flex;
  gap: 10px;
  align-items: center;
}

.date-input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.current-month-btn {
  padding: 10px 15px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.format-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.format-button {
  padding: 12px 18px;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.format-button:hover {
  background: #f5f5f5;
}

.format-button.active {
  background: #2196f3;
  color: white;
  border-color: #2196f3;
}

.element-checkboxes,
.currency-settings {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.checkbox-label:hover {
  background: #f5f5f5;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checkbox-input:checked + .checkbox-custom {
  background: #2196f3;
  border-color: #2196f3;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  color: white;
  font-weight: bold;
  font-size: 12px;
}

.image-settings {
  display: grid;
  gap: 15px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.setting-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.setting-row label {
  font-weight: 500;
  min-width: 80px;
}

.setting-select {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.export-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.preview-btn,
.export-btn,
.download-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

.preview-btn {
  background: #ff9800;
  color: white;
}

.preview-btn:hover:not(:disabled) {
  background: #f57c00;
}

.export-btn {
  background: #4caf50;
  color: white;
}

.export-btn:hover:not(:disabled) {
  background: #388e3c;
}

.download-btn {
  background: #2196f3;
  color: white;
}

.download-btn:hover:not(:disabled) {
  background: #1976d2;
}

.preview-btn:disabled,
.export-btn:disabled,
.download-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.preview-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.preview-header h3 {
  margin: 0;
  color: #333;
}

.preview-actions {
  display: flex;
  gap: 10px;
}

.copy-btn,
.clear-btn {
  padding: 8px 15px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.copy-btn:hover {
  background: #e3f2fd;
}

.clear-btn:hover {
  background: #ffebee;
}

.preview-content {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  max-height: 600px;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
  line-height: 1.5;
}

.loading {
  text-align: center;
  padding: 50px;
  color: #666;
  font-size: 16px;
}

.error {
  text-align: center;
  padding: 20px;
  color: #f44336;
  background: #ffebee;
  border-radius: 8px;
  margin: 20px 0;
}

@media (max-width: 768px) {
  .currency-blog-export {
    padding: 15px;
  }
  
  .export-actions {
    flex-direction: column;
  }
  
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .element-checkboxes,
  .currency-settings {
    grid-template-columns: 1fr;
  }
  
  .date-inputs {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
