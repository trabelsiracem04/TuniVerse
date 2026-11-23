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
    <div className="flex gap-4 p-3.5 rounded-2xl border border-gray-100 bg-white animate-pulse">
      <div className="w-28 h-28 sm:w-32 sm:h-32 rounded-xl bg-gray-200 flex-shrink-0" />
      <div className="flex flex-col justify-between flex-1 py-1">
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <div className="h-4 bg-gray-200 rounded w-1/2" />
            <div className="h-4 bg-gray-200 rounded-full w-16" />
          </div>
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-4/5" />
        </div>
        <div className="flex gap-3">
          <div className="h-3 bg-gray-200 rounded w-16" />
          <div className="h-3 bg-gray-200 rounded w-12" />
        </div>
      </div>
    </div>
  );
}
