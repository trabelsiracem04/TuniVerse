import axios from "axios";
import type { PlacesResponse, PlaceDetail, FilterOptions, PlaceFilters } from "../types";

const api = axios.create({
  baseURL: "/api/v1",
});

export const placesApi = {
  // limit=100 is the API max. With 1807 places in the DB, unfiltered queries
  // return the top 100 by recommendation_score — good enough for the MVP map.
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
