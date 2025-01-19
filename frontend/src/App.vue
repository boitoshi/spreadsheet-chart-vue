<template>
  <div id="app">
    <LineChart />
    <LineChart2 />
    <StockTable />
    <ProfitChart />
    <Spreadsheet2 />
    <Spreadsheet />
  </div>
</template>

<script setup>
import LineChart from "./components/LineChart.vue";
import LineChart2 from "./components/LineChart2.vue";
import StockTable from "./components/StockTable.vue";
import ProfitChart from "./components/ProfitChart.vue";
import Spreadsheet from "./components/Spreadsheet.vue";
import Spreadsheet2 from "./components/Spreadsheet2.vue";
</script>

<style>
#app {
  max-width: 800px;
  margin: 50px auto;
}
</style>
