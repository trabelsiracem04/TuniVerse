import { X } from "lucide-react";
import { useFilterOptions } from "../../hooks/usePlaces";
import type { PlaceFilters } from "../../types";

interface FilterBarProps {
  filters: PlaceFilters;
  onChange: (filters: PlaceFilters) => void;
}

export default function FilterBar({ filters, onChange }: FilterBarProps) {
  const { data: options } = useFilterOptions();

  const set = (key: keyof PlaceFilters, value: string) =>
    onChange({ ...filters, [key]: value });

  const clear = () =>
    onChange({ category: "", sub_category: "", city: "", search: "" });

  const hasActiveFilters =
    filters.category || filters.sub_category || filters.city || filters.search;

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-white border-b shadow-sm">

      {/* Search */}
      <div className="relative">
        <input
          type="text"
          placeholder="Search places…"
          value={filters.search}
          onChange={(e) => set("search", e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm w-52 focus:outline-none focus:ring-2 focus:ring-primary"
        />
        {filters.search && (
          <button
            onClick={() => set("search", "")}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Category */}
      <select
        value={filters.category}
        onChange={(e) => set("category", e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Categories</option>
        {options?.categories.map((c) => (
          <option key={c} value={c}>
            {c.charAt(0).toUpperCase() + c.slice(1)}
          </option>
        ))}
      </select>

      {/* Sub-category */}
      <select
        value={filters.sub_category}
        onChange={(e) => set("sub_category", e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Types</option>
        {options?.sub_categories.map((s) => (
          <option key={s} value={s}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </option>
        ))}
      </select>

      {/* City */}
      <select
        value={filters.city}
        onChange={(e) => set("city", e.target.value)}
        className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">All Cities</option>
        {options?.cities.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      {/* Active filter badges */}
      <div className="flex flex-wrap gap-2 ml-2">
        {filters.category && (
          <FilterBadge label={filters.category} onRemove={() => set("category", "")} />
        )}
        {filters.sub_category && (
          <FilterBadge label={filters.sub_category} onRemove={() => set("sub_category", "")} />
        )}
        {filters.city && (
          <FilterBadge label={filters.city} onRemove={() => set("city", "")} />
        )}
      </div>

      {/* Clear all */}
      {hasActiveFilters && (
        <button
          onClick={clear}
          className="ml-auto text-sm text-gray-500 hover:text-red-500 underline"
        >
          Clear all
        </button>
      )}
    </div>
  );
}

function FilterBadge({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="flex items-center gap-1 bg-primary/10 text-primary text-xs font-medium px-2 py-1 rounded-full">
      {label}
      <button onClick={onRemove} className="hover:text-red-500">
        <X size={11} />
      </button>
    </span>
  );
}
