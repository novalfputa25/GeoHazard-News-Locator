const MAIN_CATEGORIES = [
  "Gunungapi",
  "Gempabumi",
  "Tsunami",
  "Gerakan Tanah/Tanah Longsor",
  "Likuefaksi",
  "Abrasi dan Akresi",
  "Penurunan Muka Tanah",
  "Semburan Gas dan Lumpur",
];

const DEFAULT_FILTERS = {
  category: "all",
  date_from: "",
  date_to: "",
  province: "all",
  kabupaten: "all",
  granularity: "auto",
};

const MAP_LEGEND_CATEGORIES = [...MAIN_CATEGORIES, "Lainnya"];

const MAP_CATEGORY_STYLES = {
  Gunungapi: { color: "#dc2626", symbol: "GU" },
  Gempabumi: { color: "#d97706", symbol: "GB" },
  Tsunami: { color: "#2563eb", symbol: "TS" },
  "Gerakan Tanah/Tanah Longsor": { color: "#7c3aed", symbol: "GT" },
  Likuefaksi: { color: "#0891b2", symbol: "LF" },
  "Abrasi dan Akresi": { color: "#0f9f8f", symbol: "AA" },
  "Penurunan Muka Tanah": { color: "#a16207", symbol: "PM" },
  "Semburan Gas dan Lumpur": { color: "#db2777", symbol: "SG" },
  Lainnya: { color: "#64748b", symbol: "LN" },
};

const MAP_INDONESIA_CENTER = [-2.5, 118.5];
const MAP_INDONESIA_ZOOM = 5;

const state = { ...DEFAULT_FILTERS };
let optionsLoaded = false;
let regionOptions = { provinces: [], kabupaten_by_province: {} };
let activeRequest = 0;
let filterTimer = null;
let map = null;
let mapReady = false;
let mapInitError = "";
let markerLayer = null;
let baseLayers = {};
let activeBaseLayer = "satellite";
let fallbackAttempted = false;
let tileErrorCount = 0;
let mapTileNoticeTimer = null;
let lastMapProvince = "all";
let searchPage = 1;
const SEARCH_PER_PAGE = 10;
let searchRequest = 0;
let searchOptionsLoaded = false;

const els = {};

function cacheElements() {
  [
    "categoryFilter",
    "dateFrom",
    "dateTo",
    "provinceFilter",
    "kabupatenFilter",
    "granularityFilter",
    "applyFilter",
    "resetFilter",
    "refreshButton",
    "filterSummary",
    "filterNotice",
    "statDocuments",
    "statEvents",
    "statCategories",
    "statCategoriesNote",
    "statLocations",
    "statLocationsNote",
    "statTimes",
    "mapCanvas",
    "mapLoading",
    "mapEmpty",
    "mapEmptyText",
    "mapError",
    "mapErrorText",
    "mapTileNotice",
    "mapMarkerBadge",
    "mapStats",
    "mapLegend",
    "categoryChart",
    "trendChart",
    "trendBadge",
    "regionChart",
    "regionBadge",
    "regionNote",
    "newsBody",
    "newsTableWrap",
    "newsCount",
    "newsEmpty",
    "newsSearchForm",
    "newsQuery",
    "newsCategoryFilter",
    "newsSourceFilter",
    "newsDateFrom",
    "newsDateTo",
    "newsSearchButton",
    "newsResetButton",
    "searchResultsWrap",
    "searchResultsBody",
    "searchEmpty",
    "searchError",
    "searchErrorText",
    "searchLoading",
    "searchPagination",
    "searchPrev",
    "searchNext",
    "searchPageLabel",
    "searchCount",
    "metaNote",
    "loadingOverlay",
    "toast",
  ].forEach((id) => {
    els[id] = document.getElementById(id);
  });
}

function stateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return {
    category: params.get("category") || DEFAULT_FILTERS.category,
    date_from: params.get("date_from") || DEFAULT_FILTERS.date_from,
    date_to: params.get("date_to") || DEFAULT_FILTERS.date_to,
    province: params.get("province") || DEFAULT_FILTERS.province,
    kabupaten:
      params.get("kabupaten") ||
      params.get("kabupaten_kota") ||
      DEFAULT_FILTERS.kabupaten,
    granularity: params.get("granularity") || DEFAULT_FILTERS.granularity,
  };
}

function applyStateToControls() {
  els.categoryFilter.value = state.category;
  els.dateFrom.value = state.date_from;
  els.dateTo.value = state.date_to;
  els.provinceFilter.value = state.province;
  els.kabupatenFilter.value = state.kabupaten;
  els.granularityFilter.value = state.granularity;
}

function syncUrl() {
  const params = new URLSearchParams();
  Object.entries(state).forEach(([key, value]) => {
    if (value && value !== DEFAULT_FILTERS[key]) {
      params.set(key, value);
    }
  });
  const query = params.toString();
  const next =
    `${window.location.pathname}${query ? `?${query}` : ""}` +
    window.location.hash;
  window.history.replaceState(null, "", next);
}

function buildQuery() {
  const params = new URLSearchParams();
  Object.entries(state).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  return params.toString();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeUrl(value) {
  try {
    const parsed = new URL(String(value || ""));
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : "";
  } catch {
    return "";
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat("id-ID").format(Number(value) || 0);
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function formatDateTime(value) {
  if (!value) {
    return "Belum tersedia";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function setText(id, value) {
  if (els[id]) {
    els[id].textContent = value;
  }
}

function showLoading(show) {
  els.loadingOverlay.classList.toggle("hidden", !show);
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
}

function hideToast() {
  els.toast.classList.add("hidden");
}

function mapCategoryStyle(category) {
  return MAP_CATEGORY_STYLES[category] || MAP_CATEGORY_STYLES.Lainnya;
}

function showMapLoading(show) {
  els.mapLoading.classList.toggle("hidden", !show);
}

function setMapEmpty(show, message = "") {
  if (message) {
    els.mapEmptyText.textContent = message;
  }
  els.mapEmpty.classList.toggle("hidden", !show);
}

function showMapError(message) {
  showMapLoading(false);
  setMapEmpty(false);
  els.mapErrorText.textContent = message || "Peta gagal dimuat.";
  els.mapError.classList.remove("hidden");
}

function hideMapError() {
  els.mapError.classList.add("hidden");
}

function hideMapTileNotice() {
  window.clearTimeout(mapTileNoticeTimer);
  els.mapTileNotice.classList.add("hidden");
}

function showMapTileNotice(message) {
  window.clearTimeout(mapTileNoticeTimer);
  els.mapTileNotice.textContent = message;
  els.mapTileNotice.classList.remove("hidden");
  mapTileNoticeTimer = window.setTimeout(hideMapTileNotice, 12000);
}

function updateMapLayerButtons() {
  document.querySelectorAll("[data-map-layer]").forEach((button) => {
    const active = button.dataset.mapLayer === activeBaseLayer;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function handleMapTileError(layerKey) {
  if (!mapReady || layerKey !== activeBaseLayer) {
    return;
  }
  tileErrorCount += 1;
  if (layerKey !== "fallback" && tileErrorCount >= 4 && !fallbackAttempted) {
    fallbackAttempted = true;
    setBaseLayer("fallback");
    showMapTileNotice(
      "Layer peta gagal dimuat. Peta beralih ke OpenStreetMap; marker tetap tersedia.",
    );
    return;
  }
  if (tileErrorCount >= 8) {
    showMapTileNotice(
      "Tile peta gagal dimuat. Periksa koneksi internet; marker tetap dapat digunakan.",
    );
  }
}

function createTileLayer(url, options, layerKey) {
  const layer = L.tileLayer(url, options);
  layer.on("tileerror", () => handleMapTileError(layerKey));
  return layer;
}

function createMapBaseLayers() {
  return {
    satellite: L.layerGroup([
      createTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
          attribution:
            "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
          maxZoom: 19,
        },
        "satellite",
      ),
      createTileLayer(
        "https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: "Labels &copy; Esri",
          maxZoom: 19,
          pane: "overlayPane",
        },
        "satellite",
      ),
    ]),
    topographic: createTileLayer(
      "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
      {
        attribution:
          "Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap (CC-BY-SA)",
        maxZoom: 17,
        subdomains: "abc",
      },
      "topographic",
    ),
    fallback: createTileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
        subdomains: "abc",
      },
      "fallback",
    ),
  };
}

function setBaseLayer(layerKey) {
  if (!map || !baseLayers[layerKey]) {
    return;
  }
  if (
    activeBaseLayer &&
    baseLayers[activeBaseLayer] &&
    map.hasLayer(baseLayers[activeBaseLayer])
  ) {
    map.removeLayer(baseLayers[activeBaseLayer]);
  }
  activeBaseLayer = layerKey;
  tileErrorCount = 0;
  baseLayers[layerKey].addTo(map);
  updateMapLayerButtons();
}

function resetMapView() {
  if (map) {
    map.setView(MAP_INDONESIA_CENTER, MAP_INDONESIA_ZOOM, { animate: false });
  }
}

function fitMapToMarkers(markers) {
  if (!map || !markers.length) {
    return;
  }
  const bounds = L.latLngBounds(
    markers.map((marker) => [marker.latitude, marker.longitude]),
  );
  if (bounds.isValid()) {
    map.fitBounds(bounds.pad(0.28), { maxZoom: 9 });
  }
}

function initMap() {
  if (!els.mapCanvas) {
    return;
  }
  if (!window.L) {
    mapInitError = "Pustaka peta tidak tersedia; marker tidak dapat ditampilkan.";
    showMapError(mapInitError);
    return;
  }

  try {
    map = L.map(els.mapCanvas, {
      zoomControl: true,
      minZoom: 3,
      maxZoom: 18,
      worldCopyJump: true,
    }).setView(MAP_INDONESIA_CENTER, MAP_INDONESIA_ZOOM);
    L.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);
    baseLayers = createMapBaseLayers();
    setBaseLayer("satellite");
    mapReady = true;
    mapInitError = "";
    window.addEventListener("resize", () => map.invalidateSize());
    showMapLoading(true);
  } catch (error) {
    map = null;
    mapReady = false;
    mapInitError = error.message || "Peta gagal dimuat.";
    showMapError(mapInitError);
  }
}

function markerPopupHtml(marker) {
  const style = mapCategoryStyle(marker.category);
  const documents = marker.documents || [];
  const documentsHtml = documents.length
    ? `<ul class="map-popup-docs">${documents
        .map((document) => {
          const url = safeUrl(document.url);
          const title = escapeHtml(
            document.title || "Judul berita tidak tersedia",
          );
          const titleHtml = url
            ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${title}</a>`
            : `<span>${title}</span>`;
          return `<li>${titleHtml}<small>${escapeHtml(document.source || "Sumber tidak diketahui")}</small></li>`;
        })
        .join("")}</ul>`
    : '<p class="map-popup-empty">Belum ada berita relevan untuk kejadian ini.</p>';

  const eventTime = marker.event_time
    ? formatDateTime(marker.event_time)
    : "Waktu kejadian belum diketahui";
  const province = marker.province || "Tidak diketahui";
  const kabupaten =
    marker.kabupaten || "Kabupaten/kota belum diketahui";
  const location = marker.location_name || "Lokasi belum diketahui";
  const latitude = Number(marker.latitude).toFixed(5);
  const longitude = Number(marker.longitude).toFixed(5);
  const detailQuery = buildQuery();
  const detailHref = escapeHtml(
    `/event/${encodeURIComponent(marker.event_id)}` +
      `${detailQuery ? `?${detailQuery}` : ""}`,
  );

  return `
    <article style="--marker-color: ${style.color}">
      <h4>${escapeHtml(marker.event_title || "Judul kejadian tidak tersedia")}</h4>
      <span class="map-popup-category">${escapeHtml(marker.category || "Lainnya")}</span>
      <div class="map-popup-meta">
        <div><strong>Waktu:</strong> ${escapeHtml(eventTime)}</div>
        <div><strong>Lokasi:</strong> ${escapeHtml(location)}</div>
        <div><strong>Provinsi:</strong> ${escapeHtml(province)}</div>
        <div><strong>Kabupaten/Kota:</strong> ${escapeHtml(kabupaten)}</div>
        <div><strong>Koordinat:</strong> ${latitude}, ${longitude}</div>
        <div><strong>Berita relevan:</strong> ${formatNumber(marker.document_count || 0)}</div>
      </div>
      ${documentsHtml}
      <a class="map-popup-detail" href="${detailHref}">Lihat Detail Kejadian</a>
    </article>
  `;
}

function createMapMarker(marker) {
  const style = mapCategoryStyle(marker.category);
  const icon = L.divIcon({
    className: "map-marker-icon",
    html: `<span class="map-marker-pin" style="--marker-color: ${style.color}"><span>${style.symbol}</span></span>`,
    iconSize: [27, 32],
    iconAnchor: [13, 30],
    popupAnchor: [0, -28],
  });
  const markerTitle = marker.event_title || "Kejadian geohazard";
  const leafletMarker = L.marker(
    [Number(marker.latitude), Number(marker.longitude)],
    {
      icon,
      title: markerTitle,
      alt: markerTitle,
    },
  );
  leafletMarker.bindPopup(markerPopupHtml(marker), {
    maxWidth: 360,
    className: "map-popup",
  });
  return leafletMarker;
}

function createMarkerLayer() {
  if (typeof L.markerClusterGroup !== "function") {
    return L.layerGroup();
  }
  return L.markerClusterGroup({
    showCoverageOnHover: false,
    maxClusterRadius: 48,
    disableClusteringAtZoom: 11,
    spiderfyOnMaxZoom: true,
    removeOutsideVisibleBounds: true,
    iconCreateFunction: (cluster) => {
      const count = cluster.getChildCount();
      const size = count >= 100 ? 48 : count >= 10 ? 42 : 36;
      const variant = count >= 100 ? "large" : count >= 10 ? "medium" : "";
      return L.divIcon({
        html: `<span>${formatNumber(count)}</span>`,
        className: `map-cluster ${variant}`,
        iconSize: L.point(size, size),
      });
    },
  });
}

function renderMapStats(stats) {
  const rows = [
    ["Total kejadian", stats.total_events],
    ["Koordinat valid", stats.events_with_coordinates],
    ["Tanpa koordinat", stats.events_without_coordinates],
    ["Marker tampil", stats.marker_count],
  ];
  if (Number(stats.markers_outside_indonesia || 0) > 0) {
    rows.push(["Di luar Indonesia", stats.markers_outside_indonesia]);
  }
  els.mapStats.innerHTML = rows
    .map(
      ([label, value]) => `
        <div class="map-stat-row">
          <span>${escapeHtml(label)}</span>
          <strong>${formatNumber(value)}</strong>
        </div>
      `,
    )
    .join("");
}

function renderMapLegend(stats) {
  const counts = stats.marker_categories || {};
  els.mapLegend.innerHTML = MAP_LEGEND_CATEGORIES.map((category) => {
    const style = mapCategoryStyle(category);
    return `
      <div class="map-legend-item">
        <span class="map-legend-dot" style="--marker-color: ${style.color}">
          <span>${style.symbol}</span>
        </span>
        <span class="map-legend-name" title="${escapeHtml(category)}">${escapeHtml(category)}</span>
        <span class="map-legend-count">${formatNumber(counts[category] || 0)}</span>
      </div>
    `;
  }).join("");
}

function renderMap(mapData) {
  const markers = mapData.markers || [];
  const stats = mapData.stats || {};
  renderMapStats(stats);
  renderMapLegend(stats);
  setText(
    "mapMarkerBadge",
    `${formatNumber(stats.marker_count ?? markers.length)} marker`,
  );

  if (!mapReady) {
    showMapLoading(false);
    if (mapInitError) {
      showMapError(mapInitError);
    }
    return;
  }

  showMapLoading(false);
  hideMapError();
  if (markerLayer && map.hasLayer(markerLayer)) {
    map.removeLayer(markerLayer);
  }
  markerLayer = null;

  if (!markers.length) {
    setMapEmpty(
      true,
      Number(stats.total_events || 0) === 0
        ? "Tidak ada kejadian pada filter ini."
        : "Tidak ada kejadian dengan koordinat valid pada filter ini.",
    );
    if (state.province !== "all" || lastMapProvince !== "all") {
      resetMapView();
    }
    lastMapProvince = state.province;
    return;
  }

  setMapEmpty(false);
  markerLayer = createMarkerLayer();
  markers.forEach((marker) => {
    markerLayer.addLayer(createMapMarker(marker));
  });
  map.addLayer(markerLayer);

  const provinceFocused =
    state.province !== "all" && state.province !== "__unknown__";
  if (provinceFocused) {
    fitMapToMarkers(markers);
  } else if (state.province !== "all" || lastMapProvince !== "all") {
    resetMapView();
  }
  lastMapProvince = state.province;
}

function refreshKabupatenOptions(province, selectedKabupaten = "all") {
  const provinceValue = province || "all";
  if (provinceValue === "all") {
    els.kabupatenFilter.innerHTML =
      '<option value="all">Pilih provinsi dulu</option>';
    els.kabupatenFilter.disabled = true;
    state.kabupaten = "all";
    els.kabupatenFilter.value = "all";
    return;
  }
  if (provinceValue === "__unknown__") {
    els.kabupatenFilter.innerHTML =
      '<option value="all">Tidak ada kabupaten/kota</option>';
    els.kabupatenFilter.disabled = true;
    state.kabupaten = "all";
    els.kabupatenFilter.value = "all";
    return;
  }

  const kabupatenNames =
    regionOptions.kabupaten_by_province[provinceValue] || [];
  if (!kabupatenNames.length) {
    els.kabupatenFilter.innerHTML =
      '<option value="all">Tidak ada kabupaten/kota diketahui</option>';
    els.kabupatenFilter.disabled = true;
    state.kabupaten = "all";
    els.kabupatenFilter.value = "all";
    return;
  }

  els.kabupatenFilter.disabled = false;
  els.kabupatenFilter.innerHTML = [
    '<option value="all">Semua kabupaten/kota</option>',
    ...kabupatenNames.map(
      (name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`,
    ),
  ].join("");
  const desired = kabupatenNames.includes(selectedKabupaten)
    ? selectedKabupaten
    : "all";
  state.kabupaten = desired;
  els.kabupatenFilter.value = desired;
}

function populateOptions(options, filters) {
  const categoryNames = options.categories || [];
  const provinceNames = options.provinces || [];
  regionOptions = {
    provinces: provinceNames,
    kabupaten_by_province: options.kabupaten_by_province || {},
  };

  if (!optionsLoaded) {
    els.categoryFilter.innerHTML = [
      '<option value="all">Semua kategori</option>',
      ...categoryNames.map(
        (name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`,
      ),
    ].join("");

    els.provinceFilter.innerHTML = [
      '<option value="all">Semua wilayah</option>',
      '<option value="__unknown__">Tidak diketahui</option>',
      ...provinceNames.map(
        (name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`,
      ),
    ].join("");

    optionsLoaded = true;
  }

  const bounds = options.date_bounds || {};
  if (bounds.min) {
    els.dateFrom.min = bounds.min;
    els.dateTo.min = bounds.min;
  }
  if (bounds.max) {
    els.dateFrom.max = bounds.max;
    els.dateTo.max = bounds.max;
  }

  state.category = filters.category || "all";
  state.date_from = filters.date_from || "";
  state.date_to = filters.date_to || "";
  state.province = filters.province || "all";
  state.kabupaten = filters.kabupaten || "all";
  state.granularity = filters.granularity || "auto";
  applyStateToControls();

  if (!els.categoryFilter.value) {
    state.category = "all";
    els.categoryFilter.value = "all";
  }
  if (!els.provinceFilter.value) {
    state.province = "all";
    els.provinceFilter.value = "all";
  }
  if (!els.granularityFilter.value) {
    state.granularity = "auto";
    els.granularityFilter.value = "auto";
  }

  refreshKabupatenOptions(state.province, state.kabupaten);
  applyStateToControls();
}

function selectedLabel(select) {
  return select.options[select.selectedIndex]?.textContent || select.value;
}

function renderFilterSummary(data) {
  const category = selectedLabel(els.categoryFilter);
  const province = selectedLabel(els.provinceFilter);
  const kabupaten =
    state.kabupaten !== "all" ? selectedLabel(els.kabupatenFilter) : "";
  const dateFrom = state.date_from ? formatDate(state.date_from) : "";
  const dateTo = state.date_to ? formatDate(state.date_to) : "";
  let period = "Semua tanggal";
  if (dateFrom && dateTo) {
    period = `${dateFrom} - ${dateTo}`;
  } else if (dateFrom) {
    period = `Sejak ${dateFrom}`;
  } else if (dateTo) {
    period = `Sampai ${dateTo}`;
  }
  const trend = data.trend?.label || "Otomatis";
  els.filterSummary.innerHTML =
    `Kategori: <strong>${escapeHtml(category)}</strong> · ` +
    `Wilayah: <strong>${escapeHtml(province)}</strong>` +
    (kabupaten
      ? ` · Kab/Kota: <strong>${escapeHtml(kabupaten)}</strong>`
      : "") +
    ` · Periode: <strong>${escapeHtml(period)}</strong> · ` +
    `Tren: <strong>${escapeHtml(trend)}</strong>`;
}

function renderFilterNotice(data) {
  if (!els.filterNotice) {
    return;
  }
  const stats = data.stats || {};
  let message = "";

  if (state.province === "__unknown__") {
    message = "Menampilkan kejadian yang belum memiliki provinsi.";
  } else if (state.province !== "all" && state.kabupaten === "all") {
    const kabupatenNames =
      regionOptions.kabupaten_by_province[state.province] || [];
    if (!kabupatenNames.length) {
      message =
        `Provinsi ${state.province} belum memiliki data kabupaten/kota; ` +
        "hasil ditampilkan pada tingkat provinsi.";
    }
  }

  if (Number(stats.total_events || 0) === 0) {
    message =
      state.kabupaten !== "all"
        ? `Tidak ada kejadian untuk ${state.kabupaten}, ${state.province}.`
        : "Tidak ada kejadian pada filter ini.";
  } else if (Number(stats.total_documents || 0) === 0) {
    message = "Belum ada berita relevan pada filter ini.";
  }

  els.filterNotice.textContent = message;
  els.filterNotice.classList.toggle("hidden", !message);
}

function renderStats(stats) {
  setText("statDocuments", formatNumber(stats.total_documents));
  setText("statEvents", formatNumber(stats.total_events));
  setText("statCategories", formatNumber(stats.total_categories));
  setText(
    "statCategoriesNote",
    `dari ${formatNumber(stats.monitored_categories)} kategori dipantau`,
  );
  setText("statLocations", formatNumber(stats.events_with_location));
  setText(
    "statLocationsNote",
    `${formatNumber(stats.events_with_province)} punya provinsi · ` +
      `${formatNumber(stats.events_with_kabupaten_kota || 0)} punya kab/kota · ` +
      `${formatNumber(stats.events_without_province)} belum`,
  );
  setText("statTimes", formatNumber(stats.events_with_time));
}

function renderCategories(categories) {
  const maxValue = Math.max(
    1,
    ...categories.map((item) => Math.max(item.event_count, item.document_count)),
  );
  els.categoryChart.innerHTML = categories
    .map((item) => {
      const width = (item.event_count / maxValue) * 100;
      return `
        <div class="bar-row">
          <span class="bar-label" title="${escapeHtml(item.category)}">${escapeHtml(item.category)}</span>
          <div class="bar-track" aria-hidden="true">
            <div class="bar-fill" style="--bar-width: ${width.toFixed(2)}%"></div>
          </div>
          <span class="bar-value">${formatNumber(item.event_count)}</span>
          <span class="bar-secondary">${formatNumber(item.document_count)} berita</span>
        </div>
      `;
    })
    .join("");
}

function trendSvg(points) {
  const width = 760;
  const height = 250;
  const padding = { top: 16, right: 16, bottom: 32, left: 38 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const maxCount = Math.max(1, ...points.map((point) => point.count));
  const axisMax = Math.max(4, Math.ceil(maxCount / 4) * 4);
  const baseline = padding.top + plotHeight;

  const xFor = (index) => {
    if (points.length === 1) {
      return padding.left + plotWidth / 2;
    }
    return padding.left + (index / (points.length - 1)) * plotWidth;
  };
  const yFor = (count) =>
    padding.top + plotHeight - (count / axisMax) * plotHeight;

  const linePoints = points.map((point, index) => ({
    x: xFor(index),
    y: yFor(point.count),
    point,
  }));
  const linePath = linePoints
    .map((item, index) => `${index === 0 ? "M" : "L"} ${item.x.toFixed(2)} ${item.y.toFixed(2)}`)
    .join(" ");
  const areaPath =
    `${linePath} L ${xFor(points.length - 1).toFixed(2)} ${baseline.toFixed(2)} ` +
    `L ${xFor(0).toFixed(2)} ${baseline.toFixed(2)} Z`;

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((fraction) => {
    const y = padding.top + plotHeight - fraction * plotHeight;
    const label = Math.round(axisMax * fraction);
    return `
      <line class="chart-grid-line" x1="${padding.left}" y1="${y.toFixed(2)}"
            x2="${width - padding.right}" y2="${y.toFixed(2)}"></line>
      <text class="chart-axis-label" x="${padding.left - 8}" y="${(y + 3).toFixed(2)}"
            text-anchor="end">${label}</text>
    `;
  }).join("");

  const labelIndexes = [...new Set([
    0,
    Math.floor((points.length - 1) / 2),
    points.length - 1,
  ])].filter((index) => index >= 0);
  const xLabels = labelIndexes.map((index) => {
    const point = points[index];
    const anchor = index === 0 ? "start" : index === points.length - 1 ? "end" : "middle";
    return `<text class="chart-axis-label" x="${xFor(index).toFixed(2)}" y="${height - 10}"
      text-anchor="${anchor}">${escapeHtml(point.label)}</text>`;
  }).join("");

  const circles = linePoints.map((item) => `
    <circle class="chart-point" cx="${item.x.toFixed(2)}" cy="${item.y.toFixed(2)}" r="3.5">
      <title>${escapeHtml(item.point.label)}: ${formatNumber(item.point.count)} kejadian</title>
    </circle>
  `).join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img"
         aria-label="Grafik tren kejadian berdasarkan event_time">
      <defs>
        <linearGradient id="trendArea" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#315efb" stop-opacity="0.22"></stop>
          <stop offset="100%" stop-color="#315efb" stop-opacity="0.02"></stop>
        </linearGradient>
      </defs>
      ${gridLines}
      <path class="chart-area" d="${areaPath}"></path>
      <path class="chart-line" d="${linePath}"></path>
      ${circles}
      ${xLabels}
    </svg>
  `;
}

function renderTrend(trend) {
  const points = trend?.points || [];
  setText(
    "trendBadge",
    trend?.label || (trend?.granularity === "day" ? "Harian" : "Bulanan"),
  );
  if (!points.length) {
    els.trendChart.innerHTML =
      '<div class="chart-empty"><div><strong>Belum ada kejadian</strong><br>' +
      "Tidak ada event_time pada filter ini.</div></div>";
    return;
  }
  els.trendChart.innerHTML = trendSvg(points);
}

function renderRegions(regions) {
  const items = regions?.items || [];
  const knownItems = items.filter((item) => item.province !== "Tidak diketahui");
  setText("regionBadge", `${formatNumber(knownItems.length)} provinsi`);
  setText(
    "regionNote",
    `${formatNumber(regions?.known_total || 0)} kejadian memiliki provinsi; ` +
      `${formatNumber(regions?.unknown || 0)} tanpa provinsi.`,
  );

  if (!items.length) {
    els.regionChart.innerHTML =
      '<div class="chart-empty"><div><strong>Belum ada wilayah</strong><br>' +
      "Data provinsi belum tersedia pada filter ini.</div></div>";
    return;
  }

  const maxValue = Math.max(1, ...items.map((item) => item.count));
  els.regionChart.innerHTML = items
    .map((item) => {
      const width = (item.count / maxValue) * 100;
      const unknown = item.province === "Tidak diketahui";
      return `
        <div class="bar-row compact">
          <span class="bar-label" title="${escapeHtml(item.province)}">${escapeHtml(item.province)}</span>
          <div class="bar-track" aria-hidden="true">
            <div class="bar-fill ${unknown ? "unknown" : ""}"
                 style="--bar-width: ${width.toFixed(2)}%"></div>
          </div>
          <span class="bar-value">${formatNumber(item.count)}</span>
        </div>
      `;
    })
    .join("");
}

function renderNews(news) {
  const rows = news || [];
  setText("newsCount", `${formatNumber(rows.length)} terbaru`);
  els.newsEmpty.classList.toggle("hidden", rows.length > 0);
  els.newsTableWrap.classList.toggle("hidden", rows.length === 0);

  els.newsBody.innerHTML = rows
    .map((item) => {
      const url = safeUrl(item.url);
      const title = url
        ? `<a class="news-title" href="${escapeHtml(url)}" target="_blank"
             rel="noopener noreferrer">${escapeHtml(item.document_title)}</a>`
        : `<span class="news-title">${escapeHtml(item.document_title)}</span>`;
      const categoryClass = MAIN_CATEGORIES.includes(item.category)
        ? "category-pill in-scope"
        : "category-pill";
      const link = url
        ? `<a class="link-icon" href="${escapeHtml(url)}" target="_blank"
             rel="noopener noreferrer" aria-label="Buka sumber asli">
             <svg viewBox="0 0 24 24"><path d="M14 5h5v5"/><path d="m19 5-8 8"/>
             <path d="M19 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/></svg>
           </a>`
        : '<span class="news-date">-</span>';
      return `
        <tr>
          <td>${title}</td>
          <td class="news-source" title="${escapeHtml(item.source)}">${escapeHtml(item.source)}</td>
          <td class="news-date">${escapeHtml(formatDateTime(item.document_published_at))}</td>
          <td><span class="${categoryClass}">${escapeHtml(item.category)}</span></td>
          <td class="text-right">${link}</td>
        </tr>
      `;
    })
    .join("");
}

function searchRelevanceLabel(status) {
  const labels = {
    relevan: "Relevan",
    tidak_relevan: "Tidak relevan",
    perlu_review: "Perlu review",
  };
  return labels[status] || String(status || "Belum tersedia").replaceAll("_", " ");
}

function buildSearchQuery(page = searchPage) {
  const params = new URLSearchParams();
  const query = els.newsQuery.value.trim();
  if (query) {
    params.set("q", query);
  }
  if (els.newsCategoryFilter.value !== "all") {
    params.set("category", els.newsCategoryFilter.value);
  }
  if (els.newsSourceFilter.value !== "all") {
    params.set("source", els.newsSourceFilter.value);
  }
  if (els.newsDateFrom.value) {
    params.set("date_from", els.newsDateFrom.value);
  }
  if (els.newsDateTo.value) {
    params.set("date_to", els.newsDateTo.value);
  }
  params.set("page", String(page));
  params.set("per_page", String(SEARCH_PER_PAGE));
  return params.toString();
}

function populateSearchOptions(options) {
  if (searchOptionsLoaded) {
    return;
  }
  const categories = options.categories || [];
  const sources = options.sources || [];
  els.newsCategoryFilter.innerHTML = [
    '<option value="all">Semua kategori</option>',
    ...categories.map(
      (name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`,
    ),
  ].join("");
  els.newsSourceFilter.innerHTML = [
    '<option value="all">Semua sumber</option>',
    ...sources.map(
      (item) =>
        `<option value="${escapeHtml(item.source)}">` +
        `${escapeHtml(item.source)} (${formatNumber(item.count)})</option>`,
    ),
  ].join("");

  const bounds = options.date_bounds || {};
  if (bounds.min) {
    els.newsDateFrom.min = bounds.min;
    els.newsDateTo.min = bounds.min;
  }
  if (bounds.max) {
    els.newsDateFrom.max = bounds.max;
    els.newsDateTo.max = bounds.max;
  }
  searchOptionsLoaded = true;
}

function searchResultRow(item) {
  const url = safeUrl(item.url);
  const title = url
    ? `<a class="news-title" href="${escapeHtml(url)}" target="_blank"
         rel="noopener noreferrer">${escapeHtml(item.document_title)}</a>`
    : `<span class="news-title">${escapeHtml(item.document_title || "Judul berita tidak tersedia")}</span>`;
  const categoryClass = MAIN_CATEGORIES.includes(item.category)
    ? "category-pill in-scope"
    : "category-pill";
  const link = url
    ? `<a class="link-icon" href="${escapeHtml(url)}" target="_blank"
         rel="noopener noreferrer" aria-label="Buka sumber asli">
         <svg viewBox="0 0 24 24"><path d="M14 5h5v5"/><path d="m19 5-8 8"/>
         <path d="M19 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/></svg>
       </a>`
    : '<span class="news-date">-</span>';
  return `
    <tr>
      <td>${title}</td>
      <td class="news-source" title="${escapeHtml(item.source)}">${escapeHtml(item.source || "Tidak diketahui")}</td>
      <td class="news-date">${escapeHtml(formatDateTime(item.document_published_at))}</td>
      <td><span class="${categoryClass}">${escapeHtml(item.category || "Lainnya")}</span></td>
      <td><span class="relevance-pill" title="${escapeHtml(item.relevance_basis || "Basis relevansi belum tersedia")}">${escapeHtml(searchRelevanceLabel(item.relevance_status))}</span></td>
      <td class="text-right">${link}</td>
    </tr>
  `;
}

function renderSearchResults(payload) {
  const rows = payload.results || [];
  const pagination = payload.pagination || {};
  els.searchError.classList.add("hidden");
  setText("searchCount", `${formatNumber(pagination.total || 0)} berita`);
  els.searchResultsWrap.classList.toggle("hidden", rows.length === 0);
  els.searchEmpty.classList.toggle("hidden", rows.length > 0);
  els.searchPagination.classList.toggle(
    "hidden",
    !Number(pagination.total || 0),
  );
  els.searchResultsBody.innerHTML = rows.map(searchResultRow).join("");
  const pages = Number(pagination.pages || 0) || 1;
  setText(
    "searchPageLabel",
    `Halaman ${formatNumber(pagination.page || 1)} dari ${formatNumber(pages)} · ` +
      `${formatNumber(pagination.total || 0)} berita`,
  );
  els.searchPrev.disabled = !pagination.has_prev;
  els.searchNext.disabled = !pagination.has_next;
}

function showSearchLoading(show) {
  els.searchLoading.classList.toggle("hidden", !show);
}

function showSearchError(message) {
  els.searchErrorText.textContent = message || "Gagal mencari berita.";
  els.searchError.classList.remove("hidden");
  els.searchResultsWrap.classList.add("hidden");
  els.searchEmpty.classList.add("hidden");
  els.searchPagination.classList.add("hidden");
  setText("searchCount", "Gagal");
}

async function fetchSearch(page = 1) {
  const requestId = ++searchRequest;
  searchPage = Math.max(1, Number(page) || 1);
  els.searchError.classList.add("hidden");
  showSearchLoading(true);

  try {
    const response = await fetch(`/api/search?${buildSearchQuery(searchPage)}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(payload?.error || `HTTP ${response.status}`);
    }
    if (requestId !== searchRequest) {
      return;
    }
    populateSearchOptions(payload.options || {});
    renderSearchResults(payload);
  } catch (error) {
    if (requestId === searchRequest) {
      showSearchError(error.message || "Gagal mencari berita.");
    }
  } finally {
    if (requestId === searchRequest) {
      showSearchLoading(false);
    }
  }
}

function applySearchFilters(event) {
  if (event) {
    event.preventDefault();
  }
  if (
    els.newsDateFrom.value &&
    els.newsDateTo.value &&
    els.newsDateFrom.value > els.newsDateTo.value
  ) {
    showToast("Tanggal awal tidak boleh setelah tanggal akhir.");
    return;
  }
  fetchSearch(1);
}

function resetSearchFilters() {
  els.newsQuery.value = "";
  els.newsCategoryFilter.value = "all";
  els.newsSourceFilter.value = "all";
  els.newsDateFrom.value = "";
  els.newsDateTo.value = "";
  fetchSearch(1);
}

function bindSearchEvents() {
  els.newsSearchForm.addEventListener("submit", applySearchFilters);
  els.newsResetButton.addEventListener("click", resetSearchFilters);
  els.searchPrev.addEventListener("click", () => {
    if (!els.searchPrev.disabled) {
      fetchSearch(searchPage - 1);
    }
  });
  els.searchNext.addEventListener("click", () => {
    if (!els.searchNext.disabled) {
      fetchSearch(searchPage + 1);
    }
  });
}

function renderMeta(meta) {
  const queryMs = Number(meta?.query_ms || 0).toLocaleString("id-ID");
  els.metaNote.textContent =
    `SQLite read-only · ${queryMs} ms · ` +
    "wilayah tidak ditebak dari koordinat.";
}

function render(data) {
  renderFilterSummary(data);
  renderFilterNotice(data);
  renderStats(data.stats || {});
  renderCategories(data.categories || []);
  renderTrend(data.trend || {});
  renderRegions(data.regions || {});
  renderMap(data.map || {});
  renderNews(data.latest_news || []);
  renderMeta(data.meta || {});
}

async function fetchDashboard({ showLoader = true } = {}) {
  const requestId = ++activeRequest;
  if (showLoader) {
    showLoading(true);
  }
  hideToast();
  hideMapError();
  hideMapTileNotice();
  showMapLoading(true);

  try {
    const response = await fetch(`/api/dashboard?${buildQuery()}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(payload?.error || `HTTP ${response.status}`);
    }
    if (requestId !== activeRequest) {
      return;
    }
    populateOptions(payload.options || {}, payload.filters || {});
    render(payload);
    syncUrl();
  } catch (error) {
    if (requestId === activeRequest) {
      showToast(error.message || "Gagal memuat data dashboard.");
      showMapError(error.message || "Gagal memuat data peta.");
    }
  } finally {
    if (requestId === activeRequest) {
      showLoading(false);
    }
  }
}

function applyFilters() {
  state.category = els.categoryFilter.value || "all";
  state.date_from = els.dateFrom.value || "";
  state.date_to = els.dateTo.value || "";
  state.province = els.provinceFilter.value || "all";
  state.kabupaten = els.kabupatenFilter.value || "all";
  state.granularity = els.granularityFilter.value || "auto";

  if (state.date_from && state.date_to && state.date_from > state.date_to) {
    showToast("Tanggal awal tidak boleh setelah tanggal akhir.");
    return;
  }
  fetchDashboard();
}

function queueFilterUpdate() {
  window.clearTimeout(filterTimer);
  filterTimer = window.setTimeout(applyFilters, 220);
}

function resetFilters() {
  Object.assign(state, DEFAULT_FILTERS);
  refreshKabupatenOptions("all");
  applyStateToControls();
  resetMapView();
  lastMapProvince = "all";
  hideMapTileNotice();
  fetchDashboard();
}

function bindEvents() {
  [
    els.categoryFilter,
    els.dateFrom,
    els.dateTo,
    els.kabupatenFilter,
    els.granularityFilter,
  ].forEach((element) => {
    element.addEventListener("change", queueFilterUpdate);
  });
  els.provinceFilter.addEventListener("change", () => {
    state.province = els.provinceFilter.value || "all";
    refreshKabupatenOptions(state.province, "all");
    queueFilterUpdate();
  });
  els.applyFilter.addEventListener("click", applyFilters);
  els.resetFilter.addEventListener("click", resetFilters);
  els.refreshButton.addEventListener("click", () => fetchDashboard());
  document.querySelectorAll("[data-map-layer]").forEach((button) => {
    button.addEventListener("click", () => {
      fallbackAttempted = false;
      hideMapTileNotice();
      setBaseLayer(button.dataset.mapLayer);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  Object.assign(state, stateFromUrl());
  applyStateToControls();
  initMap();
  bindEvents();
  bindSearchEvents();
  fetchDashboard();
  fetchSearch();
});
