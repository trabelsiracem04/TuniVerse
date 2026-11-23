import axios from "axios";
import type { PlacesResponse, PlaceDetail, FilterOptions, PlaceFilters } from "../types";

const api = axios.create({
  baseURL: "/api/v1",
});

export const placesApi = {
  // Returns top 100 places by recommendation score
  getPlaces: (filters: Partial<PlaceFilters>, limit = 100, offset = 0) =>
    api
      .get<PlacesResponse>("/places", {
        params: { ...filters, limit, offset },
      })
      .then((r) => r.data),

  getPlace: (id: number) =>
    api.get<PlaceDetail>(`/places/${id}`).then((r) => r.data),

  getFilters: () =>
    api.get<FilterOptions>("/places/filters").then((r) => r.data),

  getPlaceSimilar: (id: number) =>
    api.get<PlacesResponse>(`/places/${id}/similar`).then((r) => r.data),
};
