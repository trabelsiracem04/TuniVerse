import { useParams, useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft, MapPin, Star, Eye, DollarSign } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { usePlace, useSimilarPlaces } from "../../hooks/usePlaces";
import PlaceCard from "../../components/PlaceCard";

// Fix Leaflet default icon (Vite asset bundling issue)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

export default function PlaceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const placeId = Number(id);

  const { data: place, isLoading, isError } = usePlace(placeId);
  const { data: similar } = useSimilarPlaces(placeId);

  // Preserve filter state when going back to Explore
  const handleBack = () => {
    if (location.state?.from) {
      navigate(location.state.from);
    } else {
      navigate("/explore");
    }
  };

  if (isLoading) return <DetailSkeleton />;
  if (isError || !place)
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <span className="text-5xl">😕</span>
        <p className="text-gray-500">Place not found.</p>
        <button onClick={handleBack} className="text-primary underline text-sm">
          Back to Explore
        </button>
      </div>
    );

  const allImages = [...(place.cover_image ? [place.cover_image] : []), ...place.images];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back button */}
      <div className="sticky top-0 z-10 bg-white border-b px-5 py-3 flex items-center gap-3">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-primary transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Explore
        </button>
        <span className="text-gray-300">|</span>
        <span className="text-sm font-medium text-gray-700 truncate">{place.name}</span>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-8">
        {/* Hero image gallery */}
        {allImages.length > 0 && (
          <div className="grid grid-cols-3 gap-2 h-72 rounded-2xl overflow-hidden">
            <img
              src={allImages[0]}
              alt={place.name}
              className="col-span-2 w-full h-full object-cover"
            />
            <div className="flex flex-col gap-2">
              {allImages.slice(1, 3).map((img, i) => (
                <img
                  key={i}
                  src={img}
                  alt={`${place.name} ${i + 2}`}
                  className="w-full h-full object-cover"
                  style={{ height: allImages.length > 2 ? "50%" : "100%" }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Title and meta */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <h1 className="text-3xl font-bold text-gray-900">{place.name}</h1>
            <span className="text-sm font-medium bg-primary/10 text-primary px-3 py-1 rounded-full">
              {place.category}
              {place.sub_category ? ` — ${place.sub_category}` : ""}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <MapPin size={14} className="text-primary" />
              {place.city}, {place.region}
            </span>
            {place.rate > 0 && (
              <span className="flex items-center gap-1 font-medium text-amber-600">
                <Star size={14} className="fill-amber-400 stroke-amber-400" />
                {place.rate.toFixed(1)} / 5.0
              </span>
            )}
            <span className="flex items-center gap-1 text-gray-400">
              <Eye size={14} />
              {place.view_count.toLocaleString()} views
            </span>
            {place.cost_estimate && (
              <span className="flex items-center gap-1 text-green-700 font-medium">
                <DollarSign size={14} />
                {place.cost_estimate}
              </span>
            )}
          </div>
        </div>

        {/* Description */}
        <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
          <p>{place.description}</p>
        </div>

        {/* Mini map */}
        <div className="rounded-2xl overflow-hidden h-56 shadow">
          <MapContainer
            center={[place.latitude, place.longitude]}
            zoom={13}
            style={{ height: "100%", width: "100%" }}
            zoomControl={false}
            scrollWheelZoom={false}
          >
            <TileLayer
              attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={[place.latitude, place.longitude]}>
              <Popup>{place.name}</Popup>
            </Marker>
          </MapContainer>
        </div>

        {/* Similar places */}
        {similar && similar.places.length > 0 && (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-800">You might also like</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {similar.places.map((p) => (
                <PlaceCard key={p.id} place={p} isHovered={false} onHover={() => {}} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 animate-pulse">
      <div className="h-72 bg-gray-200 rounded-2xl" />
      <div className="h-8 bg-gray-200 rounded w-2/3" />
      <div className="h-4 bg-gray-200 rounded w-1/3" />
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded" />
        <div className="h-4 bg-gray-200 rounded" />
        <div className="h-4 bg-gray-200 rounded w-5/6" />
      </div>
    </div>
  );
}
