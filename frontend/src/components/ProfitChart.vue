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
  import { ref, watch, onMounted } from 'vue'
  import { useSpreadsheetData } from '../composables/useSpreadsheetData'
  import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale, Filler } from 'chart.js'
  import { Line } from 'vue-chartjs'
  
  // Chart.jsのプラグイン登録
  ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale,Filler)
  
  // データ取得フック使用
  const { data, error, loading, fetchData } = useSpreadsheetData()

  const stockOptions = ref([])
  const selectedStock = ref('all')
  const profitChartData = ref({
    labels: [],
    datasets: [],
  })

  const updateChart = () => {
  // DOM要素の存在確認を追加
  const canvas = document.getElementById('line-chart')
  if (!canvas) return  // canvas が見つからない場合は処理中断

  const ctx = canvas.getContext('2d')
  }
  
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
  // データ取得時の処理
  watch(data, (newData) => {
    if (newData?.length) {
      // ユニークな銘柄を取得
      const uniqueStocks = [...new Set(newData.map(item => item.stock))]
      stockOptions.value = uniqueStocks
      updateProfitChartData()
    }
  })
  
  // 期間選択用の変数を追加
  const startDate = ref('2023-06')
  const endDate = ref('2024-12')
    
  // グラフデータ更新関数
  const updateProfitChartData = () => {
    if (!data.value?.length) return

  // 日付でフィルタリング
  const filteredByDate = data.value.filter(item => {
    const itemDate = item.label.substring(0, 7) // YYYY-MM-DD → YYYY-MM
    return itemDate >= startDate.value && itemDate <= endDate.value
  })

  const sortedData = [...filteredByDate].sort((a, b) => 
    new Date(a.label) - new Date(b.label)
  )
  profitChartData.value.labels = [...new Set(sortedData.map(item => item.label))]

  if (selectedStock.value === 'all') {
    const purchaseData = profitChartData.value.labels.map(date => {
      return sortedData
        .filter(item => item.label === date)
        .reduce((total, item) => total + (parseFloat(item.purchase) * parseFloat(item.quantity)), 0)
    })

    const valuationData = profitChartData.value.labels.map(date => {
      return sortedData
        .filter(item => item.label === date)
        .reduce((total, item) => total + (parseFloat(item.value) * parseFloat(item.quantity)), 0)
    })

    profitChartData.value.datasets = [
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
  } else {
    const stockData = sortedData.filter(item => item.stock === selectedStock.value)
        
    const purchaseData = profitChartData.value.labels.map(date => {
      const item = stockData.find(item => item.label === date)
      return item ? parseFloat(item.purchase) * parseFloat(item.quantity) : 0
    })

    const valuationData = profitChartData.value.labels.map(date => {
      const item = stockData.find(item => item.label === date)
      return item ? parseFloat(item.value) * parseFloat(item.quantity) : 0
    })

    profitChartData.value.datasets = [
      {
        label: '取得額',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        data: purchaseData,
        fill: false,
      },
      {
        label: '評価額',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        data: valuationData,
        fill: true,
      }
    ]
  }
};
  
  // 選択変更時にデータを更新
  watch(selectedStock, updateProfitChartData);
  
  // 初期データ取得
  onMounted(() => {
    fetchData()
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
