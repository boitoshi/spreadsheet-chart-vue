<template>
    <div>
      <h2>損益推移</h2>
      <div class="select-box">
        <label for="stock-select">銘柄を選択：</label>
        <select id="stock-select" v-model="selectedStock" @change="updateProfitChartData">
          <option value="all">すべて</option>
          <option v-for="stock in stockOptions" :key="stock" :value="stock">
            {{ stock }}
          </option>
        </select>
      </div>
      <Line :key="selectedStock" :data="profitChartData" :options="chartOptions" />
    </div>
  </template>
  
  <script setup>
  import { ref, watch } from 'vue'
  import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale, Filler } from 'chart.js'
  import { Line } from 'vue-chartjs'
  
  // Chart.jsのプラグイン登録
  ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale,Filler)
  
  // 銘柄データ（仮）
  const allStockData = ref([
    {
      name: 'DeNA',
      purchasePrice: 2000,
      currentPrices: [2100, 1500, 2200],
      stocks: 10,
    },
    {
      name: '任天堂',
      purchasePrice: 5500,
      currentPrices: [5600, 8500, 9000],
      stocks: 50,
    },
  ]);
  
  const stockOptions = ref(allStockData.value.map((stock) => stock.name));
  const selectedStock = ref('all');
  
  const profitChartData = ref({
    labels: ['1月', '2月', '3月'], // 月別ラベル
    datasets: [],
  });
  
  const chartOptions = ref({
    responsive: true,
    plugins: {
        legend: { position: 'top' },
    },
    scales: {
        y: {
        beginAtZero: true, // Y軸を0から始める
        },
    },
    });
  
  // グラフデータ更新関数
  const updateProfitChartData = () => {
    if (selectedStock.value === 'all') {
      const totalPurchaseData = allStockData.value[0].currentPrices.map((_, index) =>
        allStockData.value.reduce((total, stock) => total + stock.purchasePrice * stock.stocks, 0)
      );
      const totalValuationData = allStockData.value[0].currentPrices.map((_, index) =>
        allStockData.value.reduce((total, stock) => total + stock.currentPrices[index] * stock.stocks, 0)
      );
  
      profitChartData.value.datasets = [
        {
          label: '取得額合計',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          data: totalPurchaseData,
          fill: false, // 塗りつぶしを無効にする
        },
        {
          label: '評価額合計',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          data: totalValuationData,
          fill: true, // 塗りつぶしを有効にする
        },
      ];
    } else {
      const stock = allStockData.value.find((stock) => stock.name === selectedStock.value);
  
      profitChartData.value.datasets = [
        {
          label: '取得額',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          data: stock.currentPrices.map(() => stock.purchasePrice * stock.stocks),
          fill: false, // 塗りつぶしを無効にする
        },
        {
          label: '評価額',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          borderColor: 'rgba(54, 162, 235, 1)',
          data: stock.currentPrices.map((price) => price * stock.stocks),
          fill: true, // 塗りつぶしを有効にする
        },
      ];
    }
  };
  
  // 選択変更時にデータを更新
  watch(selectedStock, updateProfitChartData);
  
  // 初期化
  updateProfitChartData();
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
  </style>
