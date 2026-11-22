import { useQuery } from "@tanstack/react-query";
import { placesApi } from "../config/api";
import type { PlaceFilters } from "../types";

export function usePlaces(filters: Partial<PlaceFilters>) {
  return useQuery({
    queryKey: ["places", filters],
    queryFn: () => placesApi.getPlaces(filters),
    staleTime: 1000 * 30, // cache for 30 seconds
  });
}

export function usePlace(id: number) {
  return useQuery({
    queryKey: ["place", id],
    queryFn: () => placesApi.getPlace(id),
    enabled: id > 0,
  });
}

export function useFilterOptions() {
  return useQuery({
    queryKey: ["filterOptions"],
    queryFn: placesApi.getFilters,
    staleTime: 1000 * 60 * 10, // cache for 10 minutes — these rarely change
  });
}

export function useSimilarPlaces(id: number) {
  return useQuery({
    queryKey: ["similar", id],
    queryFn: () => placesApi.getPlaceSimilar(id),
    enabled: id > 0,
  });
}
