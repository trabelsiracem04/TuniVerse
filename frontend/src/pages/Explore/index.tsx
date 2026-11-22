import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import FilterBar from "../../components/FilterBar";
import PlaceCardList from "../../components/PlaceCardList";
import LeafletMap from "../../components/LeafletMap";
import { usePlaces } from "../../hooks/usePlaces";
import type { PlaceFilters } from "../../types";

export default function ExplorePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  // Read filter state from URL — makes links shareable and back-button work
  const filters: PlaceFilters = {
    category:     searchParams.get("category") ?? "",
    sub_category: searchParams.get("sub_category") ?? "",
    city:         searchParams.get("city") ?? "",
    search:       searchParams.get("search") ?? "",
  };

  const handleFilterChange = (newFilters: PlaceFilters) => {
    const params: Record<string, string> = {};
    if (newFilters.category)     params.category     = newFilters.category;
    if (newFilters.sub_category) params.sub_category = newFilters.sub_category;
    if (newFilters.city)         params.city         = newFilters.city;
    if (newFilters.search)       params.search       = newFilters.search;
    setSearchParams(params);
  };

  const { data, isLoading } = usePlaces(filters);
  const places = data?.places ?? [];

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* Header */}
      <header className="flex items-center px-5 py-3 bg-white border-b shadow-sm">
        <span className="text-lg font-bold text-primary">🌍 TuniVerse</span>
      </header>

      {/* Filter bar */}
      <FilterBar filters={filters} onChange={handleFilterChange} />

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left panel — card list */}
        <aside className="w-96 flex-shrink-0 border-r overflow-hidden flex flex-col">
          <PlaceCardList
            places={places}
            hoveredId={hoveredId}
            onHover={setHoveredId}
            isLoading={isLoading}
          />
        </aside>

        {/* Right panel — map */}
        <main className="flex-1 relative">
          <LeafletMap
            places={places}
            hoveredId={hoveredId}
            onHover={setHoveredId}
          />
        </main>

      </div>
    </div>
  );
}
