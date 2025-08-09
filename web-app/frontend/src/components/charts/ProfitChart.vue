<template>
    <div>
      <h2>損益推移</h2>
      <div class="filter-controls">
        <!-- 期間選択 -->
        <div class="date-range">
          <label>期間：</label>
          <input 
            type="month" 
            v-model="startDate"
            @change="updateProfitChartData"
          >
          <span>～</span>
          <input 
            type="month" 
            v-model="endDate"
            @change="updateProfitChartData"
          >
        </div>
        <!-- 既銘柄選択 -->
        <div class="select-box">
          <label for="stock-select">銘柄を選択：</label>
          <select id="stock-select" v-model="selectedStock" @change="updateProfitChartData">
            <option value="all">すべて</option>
            <option v-for="stock in stockOptions" :key="stock" :value="stock">
              {{ stock }}
            </option>
          </select>
        </div>
      </div>
      <Line :key="selectedStock" :data="profitChartData" :options="chartOptions" />
    </div>
</template>
  
  <script setup>
  import { ref, onMounted, watch } from 'vue'
  import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale, Filler } from 'chart.js'
  import { Line } from 'vue-chartjs'
  import { apiService } from '../../utils/api.js'
  
  // Chart.jsのプラグイン登録
  ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale, Filler)
  
  // サーバから取得した履歴データ
  const history = ref(null)
  const error = ref(null)
  const loading = ref(false)

  // 本チャートはサーバ集計（全体）に統一
  const stockOptions = ref(['all'])
  const selectedStock = ref('all')
  const profitChartData = ref({
    labels: [],
    datasets: [],
  })

  // 互換：未使用の直接描画は撤去（vue-chartjsが描画）
  
  // チャートオプション設定
  const chartOptions = ref({
    responsive: true,
    plugins: {
      legend: { position: 'top' },
    },
    scales: {
      y: {
        ticks: {
          callback: function(value) {
            return value.toLocaleString() + '円'
          },
        },
      },
    },
  })

  // 日付の変更を監視する
  watch([startDate, endDate], () => {
    updateProfitChartData()
  })
  
  // 期間選択用の変数を追加
  const startDate = ref('2023-06')
  const endDate = ref('2024-12')
    
  // グラフデータ更新関数
  const updateProfitChartData = () => {
    if (!history.value) return

    const periods = history.value.periods || []
    const totalCosts = history.value.totalCosts || []
    const totalValues = history.value.totalValues || []

    // 月フィルタ（YYYY-MMで比較）
    const indices = periods
      .map((p, i) => ({ i, m: (p || '').toString().substring(0, 7) }))
      .filter(({ m }) => (!startDate.value || m >= startDate.value) && (!endDate.value || m <= endDate.value))
      .map(({ i }) => i)

    const labels = indices.map(i => periods[i])
    const purchaseData = indices.map(i => Number(totalCosts[i] || 0))
    const valuationData = indices.map(i => Number(totalValues[i] || 0))

    profitChartData.value = {
      labels,
      datasets: [
        {
          label: '取得額合計',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          data: purchaseData,
          fill: false,
        },
        {
          label: '評価額合計',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          data: valuationData,
          fill: true,
        }
      ]
    }
  };
  
  // 選択変更（現状は all のみ）
  watch(selectedStock, updateProfitChartData)

  // 初期データ取得（バックエンド履歴）
  onMounted(async () => {
    try {
      loading.value = true
      const { data } = await apiService.getProfitHistory({ period: 'all' })
      history.value = data
      updateProfitChartData()
    } catch (e) {
      error.value = e?.message || '履歴データの取得に失敗しました'
      console.error('Profit history fetch error:', e)
    } finally {
      loading.value = false
    }
  })
  </script>
  
  <style scoped>
  h2 {
    text-align: center;
    margin-bottom: 20px;
  }
  
  .select-box {
    margin-bottom: 20px;
    text-align: center;
  }
  
  select {
    padding: 5px;
    font-size: 14px;
  }

  .filter-controls {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 20px;
  }

  .date-range {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  input[type="month"] {
    padding: 5px;
    font-size: 14px;
  }
  </style>
