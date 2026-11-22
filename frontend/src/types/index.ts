export interface PlaceCard {
  id: number;
  name: string;
  city: string;
  region: string;
  category: string;
  sub_category: string | null;
  short_desc: string;
  cover_image: string | null;
  latitude: number;
  longitude: number;
  rate: number;
  view_count: number;
  recommendation_score: number;
}

export interface PlaceDetail extends PlaceCard {
  description: string;
  images: string[];
  cost_estimate: string | null;
}

export interface PlacesResponse {
  total: number;
  places: PlaceCard[];
}

export interface FilterOptions {
  cities: string[];
  categories: string[];
  sub_categories: string[];
}

export interface PlaceFilters {
  category: string;
  sub_category: string;
  city: string;
  search: string;
}
