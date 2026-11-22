import { Routes, Route, Navigate } from "react-router-dom";
import ExplorePage from "./pages/Explore";
import PlaceDetailPage from "./pages/PlaceDetail";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/explore" replace />} />
      <Route path="/explore" element={<ExplorePage />} />
      <Route path="/place/:id" element={<PlaceDetailPage />} />
    </Routes>
  );
}
