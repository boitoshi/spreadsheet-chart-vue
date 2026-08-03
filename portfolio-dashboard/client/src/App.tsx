import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import Currency from "./pages/Currency";
import Dashboard from "./pages/Dashboard";
import Dividend from "./pages/Dividend";
import History from "./pages/History";
import Portfolio from "./pages/Portfolio";
import ReportDetail from "./pages/ReportDetail";
import Reports from "./pages/Reports";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="history" element={<History />} />
          <Route path="currency" element={<Currency />} />
          <Route path="dividend" element={<Dividend />} />
          <Route path="reports" element={<Reports />} />
          <Route path="reports/:year/:month" element={<ReportDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
