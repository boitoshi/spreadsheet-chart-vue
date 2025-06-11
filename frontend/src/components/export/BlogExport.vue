<template>
  <div class="blog-export">
    <div class="export-header">
      <h2>📝 ブログ用エクスポート</h2>
      <p>月次レポートをブログ投稿用に最適化して出力します</p>
    </div>
    
    <div class="export-options">
      <div class="option-group">
        <h3>出力形式</h3>
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
      
      <div class="option-group">
        <h3>含める要素</h3>
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
      
      <div class="option-group">
        <h3>画像設定</h3>
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
            <label>画像幅</label>
            <input 
              v-model.number="imageWidth" 
              type="number" 
              min="400" 
              max="1200"
              class="setting-input"
            >
            <span class="unit">px</span>
          </div>
        </div>
      </div>
      
      <div class="option-group">
        <h3>ブログ設定</h3>
        <div class="blog-settings">
          <div class="setting-row">
            <label>タイトル</label>
            <input 
              v-model="blogTitle" 
              type="text" 
              placeholder="投資成績レポート"
              class="setting-input"
            >
          </div>
          
          <div class="setting-row">
            <label>タグ</label>
            <input 
              v-model="blogTags" 
              type="text" 
              placeholder="投資,株式,ポートフォリオ"
              class="setting-input"
            >
          </div>
          
          <div class="setting-row">
            <label>カテゴリ</label>
            <select v-model="blogCategory" class="setting-select">
              <option value="investment">投資</option>
              <option value="portfolio">ポートフォリオ</option>
              <option value="monthly-report">月次レポート</option>
              <option value="analysis">分析</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    
    <div class="export-actions">
      <button @click="previewExport" class="preview-button">
        👁️ プレビュー
      </button>
      <button @click="exportData" class="export-button">
        💾 エクスポート実行
      </button>
    </div>
    
    <!-- プレビューモーダル -->
    <div v-if="showPreview" class="preview-modal" @click="closePreview">
      <div class="preview-content" @click.stop>
        <div class="preview-header">
          <h3>エクスポートプレビュー</h3>
          <button @click="closePreview" class="close-button">×</button>
        </div>
        <div class="preview-body">
          <div v-if="selectedFormat === 'markdown'" class="markdown-preview">
            <pre>{{ previewContent }}</pre>
          </div>
          <div v-else-if="selectedFormat === 'html'" class="html-preview" v-html="previewContent">
          </div>
          <div v-else-if="selectedFormat === 'wordpress'" class="wordpress-preview">
            <div class="wp-meta">
              <p><strong>タイトル:</strong> {{ blogTitle }}</p>
              <p><strong>カテゴリ:</strong> {{ blogCategory }}</p>
              <p><strong>タグ:</strong> {{ blogTags }}</p>
            </div>
            <div class="wp-content" v-html="previewContent"></div>
          </div>
        </div>
        <div class="preview-footer">
          <button @click="copyToClipboard" class="copy-button">
            📋 クリップボードにコピー
          </button>
          <button @click="downloadPreview" class="download-button">
            💾 ダウンロード
          </button>
        </div>
      </div>
    </div>
    
    <!-- エクスポート履歴 -->
    <div class="export-history">
      <h3>📋 エクスポート履歴</h3>
      <div class="history-list">
        <div 
          v-for="export_ in exportHistory" 
          :key="export_.id"
          class="history-item"
        >
          <div class="history-info">
            <span class="history-date">{{ formatDate(export_.date) }}</span>
            <span class="history-format">{{ export_.format }}</span>
            <span class="history-title">{{ export_.title }}</span>
          </div>
          <div class="history-actions">
            <button @click="reExport(export_)" class="re-export-button">
              🔄 再エクスポート
            </button>
            <button @click="deleteHistory(export_.id)" class="delete-button">
              🗑️ 削除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { saveAs } from 'file-saver'

export default {
  name: 'BlogExport',
  props: {
    reportData: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props, { emit }) {
    const selectedFormat = ref('markdown')
    const imageQuality = ref(0.9)
    const imageWidth = ref(800)
    const blogTitle = ref('2024年1月 投資成績レポート')
    const blogTags = ref('投資,株式,ポートフォリオ,月次レポート')
    const blogCategory = ref('investment')
    const showPreview = ref(false)
    const previewContent = ref('')
    const exportHistory = ref([])
    
    const exportFormats = [
      { id: 'markdown', name: 'Markdown', icon: '📝' },
      { id: 'html', name: 'HTML', icon: '🌐' },
      { id: 'wordpress', name: 'WordPress', icon: '📰' },
      { id: 'image', name: '画像', icon: '🖼️' }
    ]
    
    const blogElements = reactive([
      { id: 'header', name: 'ヘッダー', icon: '🎯', included: true },
      { id: 'summary', name: 'サマリーカード', icon: '📊', included: true },
      { id: 'chart', name: 'グラフ', icon: '📈', included: true },
      { id: 'portfolio', name: 'ポートフォリオ表', icon: '💼', included: true },
      { id: 'topics', name: 'トピックス', icon: '📰', included: true },
      { id: 'commentary', name: '所感', icon: '💭', included: true },
      { id: 'footer', name: 'フッター', icon: '📄', included: false }
    ])
    
    const generateMarkdown = () => {
      let content = ''
      
      if (blogElements.find(e => e.id === 'header')?.included) {
        content += `# ${blogTitle.value}\n\n`
        content += `> ポケモン世代の投資ブログ - Monthly Report\n\n`
      }
      
      if (blogElements.find(e => e.id === 'summary')?.included) {
        content += `## 📊 今月のサマリー\n\n`
        content += `| 項目 | 金額 | 変化率 |\n`
        content += `|------|------|--------|\n`
        content += `| 今月の損益 | +¥45,320 | +15.2% |\n`
        content += `| 累計損益 | +¥234,567 | +18.5% |\n`
        content += `| 総資産評価額 | ¥1,456,789 | - |\n\n`
      }
      
      if (blogElements.find(e => e.id === 'chart')?.included) {
        content += `## 📈 資産推移グラフ\n\n`
        content += `![資産推移グラフ](chart-image.png)\n\n`
      }
      
      if (blogElements.find(e => e.id === 'portfolio')?.included) {
        content += `## 💼 保有銘柄詳細\n\n`
        content += `| 銘柄 | 保有数 | 取得単価 | 現在価格 | 損益 | 損益率 |\n`
        content += `|------|--------|----------|----------|------|--------|\n`
        content += `| DeNA (2432) | 100株 | ¥2,150 | ¥2,380 | +¥23,000 | +10.7% |\n`
        content += `| 任天堂 (7974) | 50株 | ¥5,600 | ¥6,500 | +¥45,000 | +16.1% |\n\n`
      }
      
      if (blogElements.find(e => e.id === 'commentary')?.included) {
        content += `## 💭 今月の所感\n\n`
        content += `今月は全体的に好調な相場環境の中、保有銘柄すべてがプラスとなりました。\n\n`
        content += `特に任天堂は新作ゲームの好調な売れ行きを背景に大きく上昇。DeNAもAI事業への期待から堅調に推移しています。\n\n`
      }
      
      return content
    }
    
    const generateHTML = () => {
      let content = '<div class="investment-report">'
      
      if (blogElements.find(e => e.id === 'header')?.included) {
        content += `<header class="report-header">`
        content += `<h1>${blogTitle.value}</h1>`
        content += `<p class="subtitle">ポケモン世代の投資ブログ - Monthly Report</p>`
        content += `</header>`
      }
      
      if (blogElements.find(e => e.id === 'summary')?.included) {
        content += `<section class="summary-section">`
        content += `<h2>📊 今月のサマリー</h2>`
        content += `<div class="summary-cards">`
        content += `<div class="summary-card highlight">`
        content += `<div class="label">今月の損益</div>`
        content += `<div class="value">+¥45,320</div>`
        content += `<div class="change">前月比 +15.2%</div>`
        content += `</div>`
        content += `</div>`
        content += `</section>`
      }
      
      content += '</div>'
      
      return content
    }
    
    const previewExport = () => {
      switch (selectedFormat.value) {
        case 'markdown':
          previewContent.value = generateMarkdown()
          break
        case 'html':
          previewContent.value = generateHTML()
          break
        case 'wordpress':
          previewContent.value = generateHTML()
          break
        case 'image':
          previewContent.value = '画像プレビューは実装中です'
          break
      }
      showPreview.value = true
    }
    
    const closePreview = () => {
      showPreview.value = false
    }
    
    const exportData = async () => {
      const content = selectedFormat.value === 'markdown' ? generateMarkdown() : generateHTML()
      const filename = `${blogTitle.value.replace(/[^\w\s-]/g, '').replace(/\s+/g, '-')}`
      
      let blob
      let extension
      
      switch (selectedFormat.value) {
        case 'markdown':
          blob = new Blob([content], { type: 'text/markdown' })
          extension = 'md'
          break
        case 'html':
          blob = new Blob([content], { type: 'text/html' })
          extension = 'html'
          break
        case 'wordpress':
          const wpContent = JSON.stringify({
            title: blogTitle.value,
            content: content,
            category: blogCategory.value,
            tags: blogTags.value.split(',').map(tag => tag.trim())
          }, null, 2)
          blob = new Blob([wpContent], { type: 'application/json' })
          extension = 'json'
          break
        case 'image':
          alert('画像エクスポートは実装中です')
          return
      }
      
      saveAs(blob, `${filename}.${extension}`)
      
      // 履歴に追加
      const newExport = {
        id: Date.now(),
        date: new Date().toISOString(),
        format: selectedFormat.value,
        title: blogTitle.value,
        settings: {
          imageQuality: imageQuality.value,
          imageWidth: imageWidth.value,
          elements: blogElements.filter(e => e.included).map(e => e.id)
        }
      }
      
      exportHistory.value.unshift(newExport)
      
      // 親コンポーネントに通知
      emit('exported', newExport)
    }
    
    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(previewContent.value)
        alert('クリップボードにコピーしました')
      } catch (err) {
        console.error('コピーに失敗しました:', err)
        alert('コピーに失敗しました')
      }
    }
    
    const downloadPreview = () => {
      const content = previewContent.value
      const filename = `${blogTitle.value}-preview`
      const extension = selectedFormat.value === 'markdown' ? 'md' : 'html'
      const blob = new Blob([content], { type: selectedFormat.value === 'markdown' ? 'text/markdown' : 'text/html' })
      saveAs(blob, `${filename}.${extension}`)
    }
    
    const reExport = (exportItem) => {
      selectedFormat.value = exportItem.format
      blogTitle.value = exportItem.title
      imageQuality.value = exportItem.settings.imageQuality
      imageWidth.value = exportItem.settings.imageWidth
      
      // エレメント設定を復元
      blogElements.forEach(element => {
        element.included = exportItem.settings.elements.includes(element.id)
      })
      
      exportData()
    }
    
    const deleteHistory = (id) => {
      if (confirm('この履歴を削除しますか？')) {
        exportHistory.value = exportHistory.value.filter(item => item.id !== id)
      }
    }
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    return {
      selectedFormat,
      exportFormats,
      blogElements,
      imageQuality,
      imageWidth,
      blogTitle,
      blogTags,
      blogCategory,
      showPreview,
      previewContent,
      exportHistory,
      previewExport,
      closePreview,
      exportData,
      copyToClipboard,
      downloadPreview,
      reExport,
      deleteHistory,
      formatDate
    }
  }
}
</script>

<style scoped>
.blog-export {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.export-header {
  text-align: center;
  margin-bottom: 30px;
}

.export-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.export-header p {
  color: #666;
  font-size: 1.1em;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 25px;
  margin-bottom: 30px;
}

.option-group {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.option-group h3 {
  margin-bottom: 15px;
  color: #333;
  font-size: 1.1em;
}

/* フォーマットボタン */
.format-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.format-button {
  padding: 10px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

.format-button:hover {
  border-color: #667eea;
}

.format-button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* チェックボックス */
.element-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 500;
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
  position: relative;
  transition: all 0.3s ease;
}

.checkbox-input:checked + .checkbox-custom {
  background: #667eea;
  border-color: #667eea;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  color: white;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
}

/* 設定項目 */
.image-settings,
.blog-settings {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.setting-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.setting-row label {
  min-width: 80px;
  font-weight: 500;
  color: #333;
}

.setting-input,
.setting-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.setting-input:focus,
.setting-select:focus {
  outline: none;
  border-color: #667eea;
}

.unit {
  color: #666;
  font-size: 14px;
}

/* アクションボタン */
.export-actions {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 40px;
}

.preview-button,
.export-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
}

.preview-button {
  background: #6c757d;
  color: white;
}

.export-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.preview-button:hover,
.export-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

/* プレビューモーダル */
.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.preview-content {
  background: white;
  width: 90%;
  max-width: 800px;
  max-height: 80%;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.preview-header h3 {
  margin: 0;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.preview-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.markdown-preview pre {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.html-preview {
  border: 1px solid #ddd;
  padding: 15px;
  border-radius: 6px;
}

.wordpress-preview .wp-meta {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 15px;
}

.wordpress-preview .wp-content {
  border: 1px solid #ddd;
  padding: 15px;
  border-radius: 6px;
}

.preview-footer {
  display: flex;
  justify-content: center;
  gap: 15px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.copy-button,
.download-button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.copy-button {
  background: #28a745;
  color: white;
}

.download-button {
  background: #007bff;
  color: white;
}

/* エクスポート履歴 */
.export-history {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.export-history h3 {
  margin-bottom: 15px;
  color: #333;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.history-date {
  font-size: 12px;
  color: #666;
}

.history-format {
  font-weight: 600;
  color: #667eea;
}

.history-title {
  color: #333;
}

.history-actions {
  display: flex;
  gap: 8px;
}

.re-export-button,
.delete-button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.re-export-button {
  background: #007bff;
  color: white;
}

.delete-button {
  background: #dc3545;
  color: white;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .format-buttons {
    flex-direction: column;
  }
  
  .export-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .preview-content {
    width: 95%;
    max-height: 90%;
  }
  
  .history-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .history-actions {
    align-self: stretch;
    justify-content: flex-end;
  }
}
</style>