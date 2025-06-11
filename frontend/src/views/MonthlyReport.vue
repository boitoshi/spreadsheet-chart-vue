<template>
  <div class="report-container">
    <!-- ヘッダー -->
    <header class="report-header">
      <h1 class="report-title">📊 {{ reportTitle }}</h1>
      <p class="report-subtitle">ポケモン世代の投資ブログ - Monthly Report</p>
    </header>
    
    <!-- サマリーセクション -->
    <section class="summary-section">
      <div class="summary-card highlight">
        <div class="summary-label">今月の損益</div>
        <div class="summary-value">{{ formatCurrency(monthlyProfit) }}</div>
        <div class="summary-change">
          <span :class="monthlyChange >= 0 ? 'arrow-up' : 'arrow-down'">
            {{ monthlyChange >= 0 ? '▲' : '▼' }}
          </span>
          <span>前月比 {{ formatPercent(monthlyChange) }}</span>
        </div>
      </div>
      
      <div class="summary-card profit">
        <div class="summary-label">累計損益</div>
        <div class="summary-value">{{ formatCurrency(totalProfit) }}</div>
        <div class="summary-change">
          <span :class="totalReturn >= 0 ? 'arrow-up' : 'arrow-down'">
            {{ totalReturn >= 0 ? '▲' : '▼' }}
          </span>
          <span>{{ formatPercent(totalReturn) }}</span>
        </div>
      </div>
      
      <div class="summary-card">
        <div class="summary-label">総資産評価額</div>
        <div class="summary-value">{{ formatCurrency(totalValue) }}</div>
        <div class="summary-change">
          <span>投資元本: {{ formatCurrency(totalInvestment) }}</span>
        </div>
      </div>
    </section>
    
    <!-- チャートセクション -->
    <section class="chart-section">
      <h2 class="section-title">
        📈 資産推移グラフ
      </h2>
      <div class="chart-container">
        <LineChart v-if="chartData" :chart-data="chartData" />
        <div v-else class="chart-placeholder">
          グラフデータを読み込み中...
        </div>
      </div>
    </section>
    
    <!-- ポートフォリオテーブル -->
    <section class="portfolio-section">
      <h2 class="section-title">
        💼 保有銘柄詳細
      </h2>
      <div class="table-container">
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
            <tr v-for="stock in portfolioData" :key="stock.ticker">
              <td>
                <div class="stock-name">{{ stock.name }}</div>
                <div class="stock-ticker">{{ stock.ticker }}</div>
              </td>
              <td>{{ stock.quantity }}株</td>
              <td>{{ formatCurrency(stock.avgPrice) }}</td>
              <td>{{ formatCurrency(stock.currentPrice) }}</td>
              <td>{{ formatCurrency(stock.marketValue) }}</td>
              <td :class="stock.profit >= 0 ? 'positive' : 'negative'">
                {{ formatCurrency(stock.profit) }}
              </td>
              <td :class="stock.profitRate >= 0 ? 'positive' : 'negative'">
                {{ formatPercent(stock.profitRate) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    
    <!-- トピックスセクション -->
    <section class="topics-section">
      <h2 class="section-title">
        📰 今月のトピックス
      </h2>
      <div v-for="topic in topics" :key="topic.id" class="topic-item">
        <div class="topic-date">{{ formatDate(topic.date) }}</div>
        <div class="topic-title">{{ topic.title }}</div>
        <div class="topic-content">{{ topic.content }}</div>
      </div>
    </section>
    
    <!-- 所感セクション -->
    <section class="commentary-section">
      <h2 class="section-title">
        💭 今月の所感
      </h2>
      <div class="commentary-content">
        <p>{{ commentary }}</p>
      </div>
    </section>
    
    <!-- エクスポートボタン -->
    <section class="export-section">
      <div class="export-buttons">
        <button @click="exportAsPDF" class="export-button">
          📄 PDFで保存
        </button>
        <button @click="exportAsImage" class="export-button">
          🖼️ 画像で保存
        </button>
        <button @click="exportAsMarkdown" class="export-button">
          📝 Markdownで保存
        </button>
      </div>
    </section>
    
    <!-- フッター -->
    <footer class="report-footer">
      <p>このレポートをシェア</p>
      <div class="share-buttons">
        <button class="share-button">Twitter</button>
        <button class="share-button">Facebook</button>
        <button class="share-button">はてなブックマーク</button>
      </div>
      <p style="margin-top: 30px; font-size: 0.9em;">
        © 2024 ポケモン世代の投資ブログ
      </p>
    </footer>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import LineChart from '../components/charts/LineChart.vue'
import { usePortfolioData } from '../composables/usePortfolioData.js'
import { useChartExport } from '../composables/useChartExport.js'

export default {
  name: 'MonthlyReport',
  components: {
    LineChart
  },
  setup() {
    const route = useRoute()
    const month = ref(route.params.month)
    
    const { portfolioData, loadPortfolioData } = usePortfolioData()
    const { exportAsPDF, exportAsImage, exportAsMarkdown } = useChartExport()
    
    // サンプルデータ
    const monthlyProfit = ref(45320)
    const totalProfit = ref(234567)
    const totalValue = ref(1456789)
    const totalInvestment = ref(1222222)
    const monthlyChange = ref(15.2)
    const totalReturn = ref(18.5)
    const chartData = ref(null)
    
    const topics = ref([
      {
        id: 1,
        date: '2024-01-15',
        title: 'DeNA、AI事業で新たな提携を発表',
        content: 'DeNAがAI分野での事業拡大を発表。ゲーム事業との相乗効果に期待が高まり、株価は5%上昇しました。'
      },
      {
        id: 2,
        date: '2024-01-20',
        title: '任天堂、新作ゲームが世界的ヒット',
        content: '新作タイトルの売上が予想を大きく上回り、今期の業績予想を上方修正。株価は年初来高値を更新しました。'
      }
    ])
    
    const commentary = ref('今月は全体的に好調な相場環境の中、保有銘柄すべてがプラスとなりました。特に任天堂は新作ゲームの好調な売れ行きを背景に大きく上昇。DeNAもAI事業への期待から堅調に推移しています。米国株のAppleも、新製品発表への期待から上昇基調が続いています。為替も円安傾向で、ドル建て資産の評価額も押し上げられました。来月は決算シーズンを迎えるため、各社の業績動向に注目しながら、引き続き長期保有のスタンスを維持していきます。')
    
    const reportTitle = computed(() => {
      const [year, monthNum] = month.value.split('-')
      return `${year}年${monthNum}月 投資成績レポート`
    })
    
    const formatCurrency = (amount) => {
      return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: 'JPY',
        minimumFractionDigits: 0
      }).format(amount)
    }
    
    const formatPercent = (rate) => {
      return `${rate >= 0 ? '+' : ''}${rate.toFixed(1)}%`
    }
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
    }
    
    onMounted(async () => {
      await loadPortfolioData()
      // チャートデータの準備
      chartData.value = {
        labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
        datasets: [{
          label: '資産推移',
          data: [1200000, 1250000, 1300000, 1280000, 1350000, 1456789],
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4
        }]
      }
    })
    
    return {
      month,
      reportTitle,
      monthlyProfit,
      totalProfit,
      totalValue,
      totalInvestment,
      monthlyChange,
      totalReturn,
      chartData,
      portfolioData,
      topics,
      commentary,
      formatCurrency,
      formatPercent,
      formatDate,
      exportAsPDF,
      exportAsImage,
      exportAsMarkdown
    }
  }
}
</script>

<style scoped>
.report-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

/* ヘッダー */
.report-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 20px;
  text-align: center;
  margin-bottom: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.report-title {
  font-size: 2.5em;
  margin-bottom: 10px;
  font-weight: bold;
}

.report-subtitle {
  font-size: 1.2em;
  opacity: 0.9;
}

/* サマリーセクション */
.summary-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.summary-card {
  background: white;
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  transition: transform 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.summary-card.highlight {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.summary-card.profit {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.summary-label {
  font-size: 0.9em;
  opacity: 0.8;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 2em;
  font-weight: bold;
  margin-bottom: 5px;
}

.summary-change {
  font-size: 1.1em;
  display: flex;
  align-items: center;
  gap: 5px;
}

.arrow-up {
  color: #4CAF50;
}

.arrow-down {
  color: #f44336;
}

/* チャートセクション */
.chart-section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  margin-bottom: 40px;
}

.section-title {
  font-size: 1.5em;
  margin-bottom: 20px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-container {
  height: 400px;
}

.chart-placeholder {
  background: #f0f0f0;
  height: 400px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

/* ポートフォリオテーブル */
.portfolio-section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  margin-bottom: 40px;
}

.table-container {
  overflow-x: auto;
}

.portfolio-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.portfolio-table th {
  background: #f8f9fa;
  padding: 15px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #e9ecef;
}

.portfolio-table td {
  padding: 15px;
  border-bottom: 1px solid #e9ecef;
}

.portfolio-table tr:hover {
  background: #f8f9fa;
}

.stock-name {
  font-weight: 600;
  color: #333;
}

.stock-ticker {
  font-size: 0.9em;
  color: #666;
}

.positive {
  color: #4CAF50;
  font-weight: 600;
}

.negative {
  color: #f44336;
  font-weight: 600;
}

/* トピックスセクション */
.topics-section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  margin-bottom: 40px;
}

.topic-item {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 15px;
  border-left: 4px solid #667eea;
}

.topic-date {
  font-size: 0.9em;
  color: #666;
  margin-bottom: 5px;
}

.topic-title {
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}

.topic-content {
  color: #666;
  line-height: 1.8;
}

/* 所感セクション */
.commentary-section {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  margin-bottom: 40px;
}

.commentary-content {
  font-size: 1.1em;
  line-height: 1.8;
  color: #333;
}

/* エクスポートセクション */
.export-section {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.08);
  margin-bottom: 40px;
  text-align: center;
}

.export-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.export-button {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.export-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

/* フッター */
.report-footer {
  text-align: center;
  padding: 30px;
  color: #666;
}

.share-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.share-button {
  padding: 10px 20px;
  border: none;
  border-radius: 25px;
  background: #667eea;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.share-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .report-header {
    padding: 30px 20px;
  }
  
  .report-title {
    font-size: 2em;
  }
  
  .summary-section {
    grid-template-columns: 1fr;
  }
  
  .portfolio-table {
    font-size: 0.9em;
  }
  
  .portfolio-table th,
  .portfolio-table td {
    padding: 10px;
  }
  
  .export-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .export-button {
    width: 200px;
  }
}
</style>