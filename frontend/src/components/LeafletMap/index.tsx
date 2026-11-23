import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import { MapPin, Star } from "lucide-react";
import clsx from "clsx";
import type { PlaceCard } from "../../types";
import { useNavigate } from "react-router-dom";

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

// ---- Helper: auto-fit map bounds when places change ----
function FitBounds({ places }: { places: PlaceCard[] }) {
  const map = useMap();
  useEffect(() => {
    if (places.length === 0) return;
    const bounds = places.map((p) => [p.latitude, p.longitude] as [number, number]);
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [places, map]);
  return null;
}

// ---- White dot with black ring (Normal) → Glowing Gold (Hovered/Selected) ----
function createPinIcon(isHovered: boolean) {
  const size = isHovered ? 24 : 16;

  const html = isHovered
    ? `
      <div style="
        width: 24px;
        height: 24px;
        background: #e8a020;
        border: 2.5px solid #ffffff;
        border-radius: 9999px;
        box-shadow: 0 0 0 2.5px #e8a020, 0 6px 18px rgba(232, 160, 32, 0.6);
        transform: scale(1.25) translateY(-2px);
        transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        cursor: pointer;
      "></div>
    `
    : `
      <div style="
        width: 16px;
        height: 16px;
        background: #ffffff;
        border: 2.5px solid #18181b;
        border-radius: 9999px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
        transition: all 0.2s ease;
        cursor: pointer;
      "></div>
    `;

  return L.divIcon({
    html,
    className: "airbnb-map-pin",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

// ---- Single Marker with Synchronized Hover Tooltip Card ----
function PlaceMapMarker({
  place,
  isHovered,
  onHover,
  onNavigate,
}: {
  place: PlaceCard;
  isHovered: boolean;
  onHover: (id: number | null) => void;
  onNavigate: (id: number) => void;
}) {
  const markerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    const marker = markerRef.current;
    if (!marker) return;

    if (isHovered) {
      marker.openTooltip();
    } else {
      marker.closeTooltip();
    }
  }, [isHovered]);

  const pinIcon = createPinIcon(isHovered);

  return (
    <Marker
      ref={markerRef}
      position={[place.latitude, place.longitude]}
      icon={pinIcon}
      zIndexOffset={isHovered ? 1000 : 0}
      eventHandlers={{
        mouseover: () => onHover(place.id),
        mouseout: () => onHover(null),
        click: () => onNavigate(place.id),
      }}
    >
      <Tooltip
        direction="top"
        offset={[0, -18]}
        opacity={1}
        interactive={true}
        className="tuniverse-map-tooltip"
      >
        <div
          onClick={(e) => {
            e.stopPropagation();
            onNavigate(place.id);
          }}
          className="w-72 sm:w-80 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-100 p-2.5 flex gap-3 cursor-pointer transition-all duration-200 hover:scale-[1.02] text-left"
        >
          {/* Thumbnail */}
          <div className="w-20 h-20 rounded-xl overflow-hidden bg-gray-100 flex-shrink-0 relative shadow-sm">
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
              <div className="w-full h-full flex items-center justify-center bg-gray-50 text-gray-400 text-2xl">
                🏛️
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex flex-col justify-between flex-1 min-w-0 py-0.5">
            <div>
              <div className="flex items-start justify-between gap-1.5">
                <h4 className="font-semibold text-gray-900 text-sm leading-tight truncate" title={place.name}>
                  {place.name}
                </h4>
                <span
                  className={clsx(
                    "text-[10px] font-medium px-2 py-0.5 rounded-full capitalize whitespace-nowrap",
                    CATEGORY_COLORS[place.category] ?? "bg-gray-100 text-gray-600"
                  )}
                >
                  {place.category}
                </span>
              </div>
              <p className="text-[11px] text-gray-600 mt-1 line-clamp-2 leading-relaxed">
                {place.short_desc}
              </p>
            </div>

            <div className="flex items-center justify-between text-xs mt-1.5">
              <span className="flex items-center gap-1 text-[11px] text-gray-500 font-medium">
                <MapPin size={11} className="text-gray-400" />
                {place.city}
              </span>
              {place.rate > 0 && (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">
                  <Star size={10} className="fill-amber-400 stroke-amber-400" />
                  {place.rate.toFixed(1)}
                </span>
              )}
            </div>
          </div>
        </div>
      </Tooltip>
    </Marker>
  );
}

interface LeafletMapProps {
  places: PlaceCard[];
  hoveredId: number | null;
  onHover: (id: number | null) => void;
}

export default function LeafletMap({ places, hoveredId, onHover }: LeafletMapProps) {
  const navigate = useNavigate();

  return (
    <MapContainer
      center={[33.8869, 9.5375]} // center of Tunisia
      zoom={6}
      style={{ height: "100%", width: "100%" }}
      zoomControl={true}
    >
      <TileLayer
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FitBounds places={places} />

      {places.map((place) => (
        <PlaceMapMarker
          key={place.id}
          place={place}
          isHovered={hoveredId === place.id}
          onHover={onHover}
          onNavigate={(id) => navigate(`/place/${id}`)}
        />
      ))}
    </MapContainer>
  );
}
