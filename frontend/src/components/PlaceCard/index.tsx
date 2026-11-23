import { useNavigate, useLocation } from "react-router-dom";
import { MapPin, Star, Eye } from "lucide-react";
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
        "flex gap-4 p-3.5 rounded-2xl cursor-pointer transition-all border",
        isHovered
          ? "border-primary shadow-lg bg-primary/5 scale-[1.01]"
          : "border-gray-100 hover:border-gray-200 hover:shadow-md bg-white"
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
      <div className="w-28 h-28 sm:w-32 sm:h-32 flex-shrink-0 rounded-xl overflow-hidden bg-gray-100 shadow-sm relative">
        {place.cover_image ? (
          <img
            src={place.cover_image}
            alt={place.name}
            className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
            onError={(e) => {
              (e.target as HTMLImageElement).src = "/placeholder.jpg";
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-200 text-gray-400 text-3xl">
            🏛️
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex flex-col justify-between flex-1 min-w-0 py-0.5">
        <div>
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-gray-900 text-base leading-snug truncate" title={place.name}>
              {place.name}
            </h3>
            <span
              className={clsx(
                "text-xs font-medium px-2.5 py-0.5 rounded-full whitespace-nowrap capitalize",
                categoryColor
              )}
            >
              {place.category}
            </span>
          </div>

          {place.sub_category && (
            <p className="text-xs text-primary/80 font-medium capitalize mt-0.5">
              {place.sub_category}
            </p>
          )}

          <p className="text-xs text-gray-600 mt-1 line-clamp-2 leading-relaxed">
            {place.short_desc}
          </p>
        </div>

        {/* Bottom meta row */}
        <div className="flex flex-wrap items-center gap-3 mt-2 text-xs">
          <span className="flex items-center gap-1 text-gray-500 font-medium">
            <MapPin size={12} className="text-gray-400" />
            {place.city}
          </span>

          {place.rate > 0 && (
            <span className="flex items-center gap-1 font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md">
              <Star size={12} className="fill-amber-400 stroke-amber-400" />
              {place.rate.toFixed(1)}
            </span>
          )}

          {place.view_count > 0 && (
            <span className="flex items-center gap-1 text-gray-400 ml-auto">
              <Eye size={12} />
              {place.view_count.toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
