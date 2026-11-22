import { useNavigate, useLocation } from "react-router-dom";
import { MapPin, Star } from "lucide-react";
import clsx from "clsx";
import type { PlaceCard as PlaceCardType } from "../../types";

const CATEGORY_COLORS: Record<string, string> = {
  beach:         "bg-blue-100 text-blue-700",
  monument:      "bg-amber-100 text-amber-700",
  museum:        "bg-purple-100 text-purple-700",
  nature:        "bg-green-100 text-green-700",
  cultural:      "bg-rose-100 text-rose-700",
  accommodation: "bg-indigo-100 text-indigo-700",
  restaurant:    "bg-orange-100 text-orange-700",
  wellness:      "bg-teal-100 text-teal-700",
};

interface PlaceCardProps {
  place: PlaceCardType;
  isHovered: boolean;
  onHover: (id: number | null) => void;
}

export default function PlaceCard({ place, isHovered, onHover }: PlaceCardProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const categoryColor = CATEGORY_COLORS[place.category] ?? "bg-gray-100 text-gray-600";

  return (
    <div
      className={clsx(
        "flex gap-3 p-3 rounded-xl cursor-pointer transition-all border",
        isHovered
          ? "border-primary shadow-md bg-primary/5 scale-[1.01]"
          : "border-transparent hover:border-gray-200 hover:shadow-sm bg-white"
      )}
      onMouseEnter={() => onHover(place.id)}
      onMouseLeave={() => onHover(null)}
      onClick={() =>
        navigate(`/place/${place.id}`, {
          state: { from: location.pathname + location.search },
        })
      }
    >
      {/* Thumbnail */}
      <div className="w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100">
        {place.cover_image ? (
          <img
            src={place.cover_image}
            alt={place.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = "/placeholder.jpg";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300 text-2xl">
            🏛️
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-col justify-between flex-1 min-w-0">
        <div>
          <div className="flex items-start justify-between gap-1">
            <h3 className="font-semibold text-gray-900 text-sm leading-tight truncate">
              {place.name}
            </h3>
            <span
              className={clsx(
                "text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap",
                categoryColor
              )}
            >
              {place.category}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{place.short_desc}</p>
        </div>

        <div className="flex items-center gap-3 mt-1">
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <MapPin size={11} />
            {place.city}
          </span>
          {place.rate > 0 && (
            <span className="flex items-center gap-1 text-xs text-amber-600 font-medium">
              <Star size={11} className="fill-amber-400 stroke-amber-400" />
              {place.rate.toFixed(1)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
