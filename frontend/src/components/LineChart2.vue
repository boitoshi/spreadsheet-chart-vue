<template>
  <div>
    <h2>株価推移(Spreadsheet)</h2>
    <div class="select-box">
      <label for="stock-select">銘柄を選択：</label>
      <select id="stock-select" v-model="selectedStock" @change="updateChartData">
        <option value="all">すべて</option>
        <option v-for="stock in stockOptions" :key="stock" :value="stock">
          {{ stock }}
        </option>
      </select>
    </div>
    <div>
      <canvas id="line-chart"></canvas>
      <div v-if="error">{{ error.message }}</div>
      <div v-if="loading">Loading...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'; // ref をインポート
import { useSpreadsheetData } from '../composables/useSpreadsheetData';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

// データ取得フックを使用
const { data, error, loading, fetchData } = useSpreadsheetData();

// chartData を定義
const chartData = ref([]);

// 他の必要なプロパティを定義
const selectedStock = ref('all');
const stockOptions = ref([]);
const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  // 他のオプションを追加
});

// データ取得時に stockOptions を設定する
watch(data, (newData) => {
  if (newData.length) {
    console.log('Fetched Data:', newData); // データ構造を確認
    // 例: ユニークな銘柄を抽出
    const uniqueStocks = [...new Set(newData.map(item => item.stock))];
    stockOptions.value = uniqueStocks;

    // chartData を設定
    chartData.value = newData;
    
    // 初回チャートの作成
    updateChart();
  }
});

// チャートを更新する関数
const updateChart = () => {
  const filteredData = selectedStock.value === 'all' 
    ? chartData.value 
    : chartData.value.filter(item => item.stock === selectedStock.value);
  
  const labels = filteredData.map(item => item.label);
  const values = filteredData.map(item => item.value);

  // 既存のチャートを破棄
  const existingChart = Chart.getChart('line-chart');
  if (existingChart) {
    existingChart.destroy();
  }
  
  const ctx = document.getElementById('line-chart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '報告月末価格（円）',
        data: values,
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 2,
        fill: false
      }]
    },
    options: {
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
};

// セレクトボックスの変更時にチャートを更新
const updateChartData = () => {
  updateChart();
};

onMounted(() => {
  fetchData();
});
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

#line-chart {
  max-width: 800px;
  margin: 50px auto;
}
</style>
