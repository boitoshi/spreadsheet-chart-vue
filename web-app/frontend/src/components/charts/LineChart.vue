<template>
  <div>
    <h2>株価推移</h2>
    <div class="select-box">
      <label for="stock-select">銘柄を選択：</label>
      <select id="stock-select" v-model="selectedStock" @change="updateChartData">
        <option value="all">すべて</option>
        <option v-for="stock in stockOptions" :key="stock" :value="stock">
          {{ stock }}
        </option>
      </select>
    </div>
    <Line :key="selectedStock" :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale } from 'chart.js'
import { Line } from 'vue-chartjs'

// Chart.jsのプラグイン登録
ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, LinearScale, CategoryScale)

//銘柄データ（ダミー）
const allStockData = ref([
  { name: 'トヨタ自動車', data: [2500, 2600, 2700, 2750, 2800, 2850] },
  { name: 'ソフトバンク', data: [1200, 1180, 1150, 1200, 1150, 1170] },
  { name: '任天堂', data: [5600, 5800, 6000, 6100, 6200, 6150] },
  { name: 'DeNA', data: [2100, 2200, 2250, 2300, 2350, 2400] },
]);

const stockOptions = ref(allStockData.value.map((stock) => stock.name));
const selectedStock = ref('all');

const chartData = ref({
  labels: ['1月', '2月', '3月', '4月', '5月', '6月'], // 月別ラベル
  datasets: allStockData.value.map((stock, index) => {
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'];
    return {
      label: stock.name,
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length],
      data: stock.data,
      fill: false,
      tension: 0.1
    };
  }),
});

const chartOptions = ref({
  responsive: true,
  // 他のオプションをここに追加
});

// グラフデータ更新関数
const updateChartData = () => {
  const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'];
  
  let updatedDatasets;

  if (selectedStock.value === 'all') {
    updatedDatasets = allStockData.value.map((stock, index) => ({
      label: stock.name,
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length],
      data: stock.data,
      fill: false,
      tension: 0.1
    }));
  } else {
    const stockIndex = allStockData.value.findIndex(stock => stock.name === selectedStock.value);
    const stock = allStockData.value[stockIndex];
    
    if (stock) {
      updatedDatasets = [{
        label: stock.name,
        backgroundColor: colors[stockIndex % colors.length],
        borderColor: colors[stockIndex % colors.length],
        data: stock.data,
        fill: false,
        tension: 0.1
      }];
    } else {
      console.warn("選択した銘柄がデータに見つかりません: ", selectedStock.value);
      updatedDatasets = [];
    }
  }

  // 新しいオブジェクトとして設定
  chartData.value = {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    datasets: updatedDatasets,
  };
};

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
