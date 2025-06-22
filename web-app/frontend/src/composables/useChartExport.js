import { ref } from 'vue'
import html2canvas from 'html2canvas'
import { saveAs } from 'file-saver'
import { marked } from 'marked'

export function useChartExport() {
  const isExporting = ref(false)
  const exportProgress = ref(0)
  
  /**
   * 指定した要素を画像として出力
   */
  const exportAsImage = async (element, options = {}) => {
    isExporting.value = true
    exportProgress.value = 0
    
    try {
      const defaultOptions = {
        quality: 0.9,
        width: 800,
        height: 600,
        backgroundColor: '#ffffff',
        scale: 2 // Retina対応
      }
      
      const config = { ...defaultOptions, ...options }
      
      exportProgress.value = 25
      
      // 要素が文字列の場合はセレクタとして扱う
      const targetElement = typeof element === 'string' 
        ? document.querySelector(element) 
        : element
      
      if (!targetElement) {
        throw new Error('エクスポート対象の要素が見つかりません')
      }
      
      exportProgress.value = 50
      
      // html2canvasで画像生成
      const canvas = await html2canvas(targetElement, {
        backgroundColor: config.backgroundColor,
        scale: config.scale,
        useCORS: true,
        allowTaint: true,
        width: config.width,
        height: config.height,
        logging: false
      })
      
      exportProgress.value = 75
      
      // Blobに変換
      const blob = await new Promise(resolve => {
        canvas.toBlob(resolve, 'image/png', config.quality)
      })
      
      exportProgress.value = 100
      
      // ファイル名生成
      const filename = options.filename || `chart-export-${Date.now()}.png`
      
      // ダウンロード
      saveAs(blob, filename)
      
      return {
        success: true,
        blob,
        canvas,
        filename
      }
      
    } catch (error) {
      console.error('画像エクスポートエラー:', error)
      throw error
    } finally {
      isExporting.value = false
      exportProgress.value = 0
    }
  }
  
  /**
   * レポート全体をPDF風のHTMLとして出力
   */
  const exportAsPDF = async (reportData, options = {}) => {
    isExporting.value = true
    
    try {
      const defaultOptions = {
        format: 'A4',
        orientation: 'portrait',
        margin: '20mm',
        fontSize: '12pt'
      }
      
      const config = { ...defaultOptions, ...options }
      
      // HTMLテンプレート生成
      const htmlContent = generatePDFHTML(reportData, config)
      
      // Blobとして出力
      const blob = new Blob([htmlContent], { type: 'text/html' })
      const filename = options.filename || `report-${Date.now()}.html`
      
      saveAs(blob, filename)
      
      return {
        success: true,
        blob,
        html: htmlContent,
        filename
      }
      
    } catch (error) {
      console.error('PDFエクスポートエラー:', error)
      throw error
    } finally {
      isExporting.value = false
    }
  }
  
  /**
   * Markdownファイルとして出力
   */
  const exportAsMarkdown = async (reportData, options = {}) => {
    isExporting.value = true
    
    try {
      const markdown = generateMarkdown(reportData, options)
      
      const blob = new Blob([markdown], { type: 'text/markdown' })
      const filename = options.filename || `report-${Date.now()}.md`
      
      saveAs(blob, filename)
      
      return {
        success: true,
        blob,
        markdown,
        filename
      }
      
    } catch (error) {
      console.error('Markdownエクスポートエラー:', error)
      throw error
    } finally {
      isExporting.value = false
    }
  }
  
  /**
   * 複数のチャートを一括で画像出力
   */
  const exportMultipleCharts = async (chartSelectors, options = {}) => {
    isExporting.value = true
    const results = []
    
    try {
      for (let i = 0; i < chartSelectors.length; i++) {
        exportProgress.value = (i / chartSelectors.length) * 100
        
        const selector = chartSelectors[i]
        const chartOptions = {
          ...options,
          filename: `chart-${i + 1}-${Date.now()}.png`
        }
        
        const result = await exportAsImage(selector, chartOptions)
        results.push(result)
        
        // 少し待機（ブラウザの負荷軽減）
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      return {
        success: true,
        results,
        count: results.length
      }
      
    } catch (error) {
      console.error('一括エクスポートエラー:', error)
      throw error
    } finally {
      isExporting.value = false
      exportProgress.value = 0
    }
  }
  
  /**
   * WordPress投稿用のJSONデータを生成
   */
  const exportForWordPress = async (reportData, options = {}) => {
    isExporting.value = true
    
    try {
      const wpData = {
        title: options.title || 'Monthly Investment Report',
        content: generateWordPressContent(reportData),
        excerpt: options.excerpt || '',
        status: 'draft',
        categories: options.categories || ['投資', 'ポートフォリオ'],
        tags: options.tags || ['月次レポート', '株式投資', '資産運用'],
        featured_media: null,
        meta: {
          custom_fields: {
            report_month: reportData.month || '',
            total_profit: reportData.totalProfit || 0,
            total_return: reportData.totalReturn || 0
          }
        }
      }
      
      const json = JSON.stringify(wpData, null, 2)
      const blob = new Blob([json], { type: 'application/json' })
      const filename = options.filename || `wordpress-post-${Date.now()}.json`
      
      saveAs(blob, filename)
      
      return {
        success: true,
        blob,
        data: wpData,
        filename
      }
      
    } catch (error) {
      console.error('WordPressエクスポートエラー:', error)
      throw error
    } finally {
      isExporting.value = false
    }
  }
  
  /**
   * PDF用HTMLテンプレート生成
   */
  const generatePDFHTML = (reportData, config) => {
    return `
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${reportData.title || 'Investment Report'}</title>
    <style>
        @page {
            size: ${config.format};
            margin: ${config.margin};
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
            font-size: ${config.fontSize};
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .report-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        
        .report-title {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        .report-subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .summary-section {
            margin-bottom: 30px;
        }
        
        .summary-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .summary-table th,
        .summary-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .summary-table th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        
        .positive {
            color: #28a745;
            font-weight: 600;
        }
        
        .negative {
            color: #dc3545;
            font-weight: 600;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin: 30px 0 15px 0;
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 10px;
        }
        
        .chart-placeholder {
            width: 100%;
            height: 300px;
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            margin: 20px 0;
        }
        
        .portfolio-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        .portfolio-table th,
        .portfolio-table td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        
        .portfolio-table th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        
        .commentary-section {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        .footer {
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }
        
        @media print {
            .page-break {
                page-break-before: always;
            }
        }
    </style>
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <h1 class="report-title">${reportData.title || 'Monthly Investment Report'}</h1>
            <p class="report-subtitle">Generated on ${new Date().toLocaleDateString('ja-JP')}</p>
        </header>
        
        <section class="summary-section">
            <h2 class="section-title">📊 サマリー</h2>
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>項目</th>
                        <th>金額</th>
                        <th>変化率</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>今月の損益</td>
                        <td class="positive">+¥${(reportData.monthlyProfit || 45320).toLocaleString()}</td>
                        <td class="positive">+${(reportData.monthlyChange || 15.2).toFixed(1)}%</td>
                    </tr>
                    <tr>
                        <td>累計損益</td>
                        <td class="positive">+¥${(reportData.totalProfit || 234567).toLocaleString()}</td>
                        <td class="positive">+${(reportData.totalReturn || 18.5).toFixed(1)}%</td>
                    </tr>
                    <tr>
                        <td>総資産評価額</td>
                        <td>¥${(reportData.totalValue || 1456789).toLocaleString()}</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section class="chart-section">
            <h2 class="section-title">📈 資産推移</h2>
            <div class="chart-placeholder">
                [チャート画像をここに挿入]
            </div>
        </section>
        
        <section class="portfolio-section page-break">
            <h2 class="section-title">💼 ポートフォリオ詳細</h2>
            <table class="portfolio-table">
                <thead>
                    <tr>
                        <th>銘柄</th>
                        <th>保有数</th>
                        <th>取得単価</th>
                        <th>現在価格</th>
                        <th>評価額</th>
                        <th>損益</th>
                        <th>損益率</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>DeNA (2432)</td>
                        <td>100株</td>
                        <td>¥2,150</td>
                        <td>¥2,380</td>
                        <td>¥238,000</td>
                        <td class="positive">+¥23,000</td>
                        <td class="positive">+10.7%</td>
                    </tr>
                    <tr>
                        <td>任天堂 (7974)</td>
                        <td>50株</td>
                        <td>¥5,600</td>
                        <td>¥6,500</td>
                        <td>¥325,000</td>
                        <td class="positive">+¥45,000</td>
                        <td class="positive">+16.1%</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section class="commentary-section">
            <h2 class="section-title">💭 所感</h2>
            <p>${reportData.commentary || '今月は全体的に好調な結果となりました。'}</p>
        </section>
        
        <footer class="footer">
            <p>© ${new Date().getFullYear()} ポケモン世代の投資ブログ | Generated with Vue.js Portfolio Tracker</p>
        </footer>
    </div>
</body>
</html>
    `
  }
  
  /**
   * Markdown形式のレポート生成
   */
  const generateMarkdown = (reportData, options = {}) => {
    const date = new Date().toLocaleDateString('ja-JP')
    
    return `# ${reportData.title || 'Monthly Investment Report'}

> Generated on ${date}

## 📊 今月のサマリー

| 項目 | 金額 | 変化率 |
|------|------|--------|
| 今月の損益 | +¥${(reportData.monthlyProfit || 45320).toLocaleString()} | +${(reportData.monthlyChange || 15.2).toFixed(1)}% |
| 累計損益 | +¥${(reportData.totalProfit || 234567).toLocaleString()} | +${(reportData.totalReturn || 18.5).toFixed(1)}% |
| 総資産評価額 | ¥${(reportData.totalValue || 1456789).toLocaleString()} | - |

## 📈 資産推移グラフ

![資産推移グラフ](chart-image.png)

*※ 画像は別途添付してください*

## 💼 保有銘柄詳細

| 銘柄 | 保有数 | 取得単価 | 現在価格 | 評価額 | 損益 | 損益率 |
|------|--------|----------|----------|--------|------|--------|
| DeNA (2432) | 100株 | ¥2,150 | ¥2,380 | ¥238,000 | +¥23,000 | +10.7% |
| 任天堂 (7974) | 50株 | ¥5,600 | ¥6,500 | ¥325,000 | +¥45,000 | +16.1% |

## 💭 今月の所感

${reportData.commentary || '今月は全体的に好調な結果となりました。'}

---

*このレポートは [Vue.js Portfolio Tracker](https://github.com/username/portfolio-tracker) で生成されました。*

## タグ

#投資 #ポートフォリオ #月次レポート #株式投資
`
  }
  
  /**
   * WordPress投稿用コンテンツ生成
   */
  const generateWordPressContent = (reportData) => {
    const htmlContent = `
<div class="investment-report">
    <div class="summary-cards">
        <div class="summary-card highlight">
            <h4>今月の損益</h4>
            <p class="amount positive">+¥${(reportData.monthlyProfit || 45320).toLocaleString()}</p>
            <p class="change">前月比 +${(reportData.monthlyChange || 15.2).toFixed(1)}%</p>
        </div>
        
        <div class="summary-card">
            <h4>累計損益</h4>
            <p class="amount positive">+¥${(reportData.totalProfit || 234567).toLocaleString()}</p>
            <p class="change">+${(reportData.totalReturn || 18.5).toFixed(1)}%</p>
        </div>
        
        <div class="summary-card">
            <h4>総資産評価額</h4>
            <p class="amount">¥${(reportData.totalValue || 1456789).toLocaleString()}</p>
            <p class="change">投資元本: ¥${(reportData.totalInvestment || 1222222).toLocaleString()}</p>
        </div>
    </div>
    
    <h3>📈 資産推移</h3>
    [chart_placeholder]
    
    <h3>💼 保有銘柄</h3>
    <table class="portfolio-table">
        <thead>
            <tr>
                <th>銘柄</th>
                <th>損益</th>
                <th>損益率</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>DeNA (2432)</td>
                <td class="positive">+¥23,000</td>
                <td class="positive">+10.7%</td>
            </tr>
            <tr>
                <td>任天堂 (7974)</td>
                <td class="positive">+¥45,000</td>
                <td class="positive">+16.1%</td>
            </tr>
        </tbody>
    </table>
    
    <h3>💭 今月の所感</h3>
    <p>${reportData.commentary || '今月は全体的に好調な結果となりました。'}</p>
</div>
    `
    
    return htmlContent
  }
  
  return {
    isExporting,
    exportProgress,
    exportAsImage,
    exportAsPDF,
    exportAsMarkdown,
    exportMultipleCharts,
    exportForWordPress
  }
}