import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import type { PlaceCard } from "../../types";
import { useNavigate } from "react-router-dom";

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

// ---- Score → marker visual ----
function markerStyle(score: number, isHovered: boolean) {
  // radius: 6 (low score) → 14 (high score)
  const radius = 6 + score * 8;
  // color: low = cool blue, high = warm orange/red
  const hue = Math.round(200 - score * 160); // 200 (blue) → 40 (orange)
  return {
    radius: isHovered ? radius + 4 : radius,
    pathOptions: {
      color: isHovered ? "#1a7f5a" : `hsl(${hue}, 80%, 50%)`,
      fillColor: isHovered ? "#1a7f5a" : `hsl(${hue}, 80%, 60%)`,
      fillOpacity: 0.85,
      weight: isHovered ? 3 : 1.5,
    },
  };
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
      center={[33.8869, 9.5375]}  // center of Tunisia
      zoom={6}
      style={{ height: "100%", width: "100%" }}
      zoomControl={true}
    >
      <TileLayer
        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <FitBounds places={places} />

      {places.map((place) => {
        const { radius, pathOptions } = markerStyle(
          place.recommendation_score,
          hoveredId === place.id
        );
        return (
          <CircleMarker
            key={place.id}
            center={[place.latitude, place.longitude]}
            radius={radius}
            pathOptions={pathOptions}
            eventHandlers={{
              mouseover: () => onHover(place.id),
              mouseout: () => onHover(null),
              click: () => navigate(`/place/${place.id}`),
            }}
          >
            <Popup>
              <div className="flex flex-col gap-1 w-36">
                {place.cover_image && (
                  <img
                    src={place.cover_image}
                    alt={place.name}
                    className="w-full h-20 object-cover rounded"
                  />
                )}
                <span className="font-semibold text-sm">{place.name}</span>
                <span className="text-xs text-gray-500">{place.city}</span>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
