import type { PlaceCard } from "../../types";
import PlaceCardComponent from "../PlaceCard";

interface PlaceCardListProps {
  places: PlaceCard[];
  hoveredId: number | null;
  onHover: (id: number | null) => void;
  isLoading: boolean;
}

export default function PlaceCardList({
  places,
  hoveredId,
  onHover,
  isLoading,
}: PlaceCardListProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3 p-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (places.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400 gap-3">
        <span className="text-5xl">🔍</span>
        <p className="text-sm font-medium">No places match your filters.</p>
        <p className="text-xs">Try clearing some filters or searching for something else.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-3 overflow-y-auto h-full">
      <p className="text-xs text-gray-400 px-1 mb-1">{places.length} places found</p>
      {places.map((place) => (
        <PlaceCardComponent
          key={place.id}
          place={place}
          isHovered={hoveredId === place.id}
          onHover={onHover}
        />
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="flex gap-3 p-3 rounded-xl border border-gray-100 animate-pulse">
      <div className="w-20 h-20 rounded-lg bg-gray-200 flex-shrink-0" />
      <div className="flex flex-col gap-2 flex-1">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-3 bg-gray-200 rounded w-full" />
        <div className="h-3 bg-gray-200 rounded w-2/3" />
      </div>
    </div>
  );
}
