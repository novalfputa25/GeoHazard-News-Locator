const els = {};

function cacheElements() {
  [
    "backLink",
    "mapLink",
    "detailContent",
    "eventTitle",
    "eventSummary",
    "eventCategory",
    "eventStatus",
    "eventVerification",
    "eventMeta",
    "eventLocations",
    "eventLocationsEmpty",
    "eventAttributes",
    "eventAttributesEmpty",
    "supportingNewsBody",
    "supportingNewsWrap",
    "supportingNewsCount",
    "supportingNewsEmpty",
    "eventNotes",
    "eventSourceNote",
    "metaNote",
    "detailLoading",
    "detailError",
    "detailErrorText",
  ].forEach((id) => {
    els[id] = document.getElementById(id);
  });
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

function formatDateTime(value) {
  if (!value) {
    return "Belum tersedia";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function humanize(value, fallback = "Belum tersedia") {
  const text = String(value ?? "").trim();
  if (!text) {
    return fallback;
  }
  return text.replaceAll("_", " ");
}

function setText(id, value) {
  if (els[id]) {
    els[id].textContent = value;
  }
}

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

function categoryClass(category) {
  return MAIN_CATEGORIES.includes(category)
    ? "category-pill in-scope"
    : "category-pill";
}

function relevanceLabel(status) {
  const labels = {
    relevan: "Relevan",
    tidak_relevan: "Tidak relevan",
    perlu_review: "Perlu review",
  };
  return labels[status] || humanize(status);
}

function eventTimeText(time) {
  if (!time) {
    return "Waktu kejadian belum diketahui";
  }
  const start = time.event_time || time.event_time_start || "";
  const end = time.event_time_end || "";
  if (start && end && end !== start) {
    return `${formatDateTime(start)} - ${formatDateTime(end)}`;
  }
  return start ? formatDateTime(start) : "Waktu kejadian belum diketahui";
}

function eventIdFromPath() {
  const match = window.location.pathname.match(/^\/event\/(.+)$/);
  if (!match) {
    return "";
  }
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

function setupNavigation() {
  const query = window.location.search || "";
  const dashboardUrl = `/${query}`;
  els.backLink.href = dashboardUrl;
  els.mapLink.href = `${dashboardUrl}#peta`;
}

function renderMeta(data) {
  const event = data.event || {};
  const time = data.time || null;
  const categories = (data.categories || [])
    .map((item) => item.category_name)
    .filter(Boolean);
  const rows = [
    ["Waktu kejadian", eventTimeText(time)],
    ["Presisi waktu", humanize(time?.event_time_precision)],
    ["Sumber utama", event.primary_source_name || "Belum tersedia"],
    ["Jenis waktu", humanize(time?.event_time_kind)],
    ["Pelaporan pertama", formatDateTime(event.event_first_reported_at)],
    ["Pembaruan terakhir", formatDateTime(event.event_last_updated_at)],
    ["Kategori", categories.length ? categories.join(", ") : "Belum tersedia"],
    ["ID kejadian", event.event_id || "Belum tersedia"],
  ];
  els.eventMeta.innerHTML = rows
    .map(
      ([label, value]) => `
        <div>
          <dt>${escapeHtml(label)}</dt>
          <dd>${escapeHtml(value)}</dd>
        </div>
      `,
    )
    .join("");
}

function renderLocations(locations) {
  const items = locations || [];
  els.eventLocationsEmpty.classList.toggle("hidden", items.length > 0);
  els.eventLocations.classList.toggle("hidden", items.length === 0);
  if (!items.length) {
    els.eventLocations.innerHTML = "";
    return;
  }

  els.eventLocations.innerHTML = items
    .map((location) => {
      const latitude = Number(location.latitude);
      const longitude = Number(location.longitude);
      const hasCoordinates =
        location.latitude !== null &&
        location.longitude !== null &&
        Number.isFinite(latitude) &&
        Number.isFinite(longitude);
      const coordinateText = hasCoordinates
        ? `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`
        : "Koordinat belum tersedia";
      const insideLabels = {
        ya: "Di dalam Indonesia",
        tidak: "Di luar Indonesia",
        tidak_diketahui: "Belum diketahui",
      };
      return `
        <article class="detail-location">
          <strong>${escapeHtml(location.location_name || "Nama lokasi belum tersedia")}</strong>
          <span class="detail-location-role">${escapeHtml(humanize(location.location_role))}</span>
          <dl>
            <div><dt>Provinsi</dt><dd>${escapeHtml(location.province || "Belum tersedia")}</dd></div>
            <div><dt>Kabupaten/Kota</dt><dd>${escapeHtml(location.kabupaten || "Belum tersedia")}</dd></div>
            <div><dt>Kecamatan</dt><dd>${escapeHtml(location.kecamatan || "Belum tersedia")}</dd></div>
            <div><dt>Desa/Kelurahan</dt><dd>${escapeHtml(location.desa_kelurahan || "Belum tersedia")}</dd></div>
            <div><dt>Koordinat</dt><dd>${escapeHtml(coordinateText)}</dd></div>
            <div><dt>Status koordinat</dt><dd>${escapeHtml(humanize(location.coordinate_status))}</dd></div>
            <div><dt>Wilayah Indonesia</dt><dd>${escapeHtml(insideLabels[location.is_inside_indonesia] || humanize(location.is_inside_indonesia))}</dd></div>
          </dl>
        </article>
      `;
    })
    .join("");
}

function renderAttributes(attributes) {
  const items = attributes || [];
  els.eventAttributesEmpty.classList.toggle("hidden", items.length > 0);
  els.eventAttributes.classList.toggle("hidden", items.length === 0);
  if (!items.length) {
    els.eventAttributes.innerHTML = "";
    return;
  }

  els.eventAttributes.innerHTML = items
    .map((attribute) => {
      const value = [attribute.attribute_value, attribute.attribute_unit]
        .filter((part) => String(part || "").trim())
        .join(" ");
      const source = attribute.source_name || attribute.source_institution;
      return `
        <div class="detail-attribute">
          <span>${escapeHtml(humanize(attribute.attribute_name))}</span>
          <strong>${escapeHtml(value || "Belum tersedia")}</strong>
          ${source ? `<small>${escapeHtml(source)}</small>` : ""}
        </div>
      `;
    })
    .join("");
}

function supportingNewsRow(item) {
  const url = safeUrl(item.url);
  const title = url
    ? `<a class="news-title" href="${escapeHtml(url)}" target="_blank"
         rel="noopener noreferrer">${escapeHtml(item.document_title)}</a>`
    : `<span class="news-title">${escapeHtml(item.document_title || "Judul berita tidak tersedia")}</span>`;
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
      <td><span class="${categoryClass(item.category)}">${escapeHtml(item.category || "Lainnya")}</span></td>
      <td><span class="relevance-pill" title="${escapeHtml(item.relevance_basis || "Basis relevansi belum tersedia")}">${escapeHtml(relevanceLabel(item.relevance_status))}</span></td>
      <td class="text-right">${link}</td>
    </tr>
  `;
}

function renderSupportingNews(items) {
  const rows = items || [];
  setText("supportingNewsCount", `${formatNumber(rows.length)} berita`);
  els.supportingNewsWrap.classList.toggle("hidden", rows.length === 0);
  els.supportingNewsEmpty.classList.toggle("hidden", rows.length > 0);
  els.supportingNewsBody.innerHTML = rows.map(supportingNewsRow).join("");
}

function renderDetail(data) {
  const event = data.event || {};
  setText("eventTitle", event.event_title || "Judul kejadian tidak tersedia");
  setText(
    "eventSummary",
    event.event_summary || "Deskripsi kejadian belum tersedia.",
  );
  setText("eventCategory", data.primary_category || "Kategori belum tersedia");
  setText("eventStatus", humanize(event.event_status));
  setText(
    "eventVerification",
    [event.event_verification_level, event.event_verification_status]
      .filter((value) => String(value || "").trim())
      .map((value) => humanize(value))
      .join(" · ") || "Belum tersedia",
  );
  renderMeta(data);
  renderLocations(data.locations);
  renderAttributes(data.attributes);
  renderSupportingNews(data.supporting_news);
  setText("eventNotes", event.event_notes || "Catatan kejadian belum tersedia.");
  setText(
    "eventSourceNote",
    event.primary_source_name
      ? `Sumber utama: ${event.primary_source_name}`
      : "Sumber utama belum tersedia.",
  );
  const queryMs = Number(data.meta?.query_ms || 0).toLocaleString("id-ID");
  setText(
    "metaNote",
    `SQLite read-only · ${queryMs} ms · Waktu publikasi berita bukan waktu kejadian.`,
  );
}

function showError(message) {
  els.detailLoading.classList.add("hidden");
  els.detailContent.classList.add("hidden");
  els.detailErrorText.textContent = message;
  els.detailError.classList.remove("hidden");
}

async function loadDetail() {
  const eventId = eventIdFromPath();
  if (!eventId) {
    showError("ID kejadian tidak ditemukan pada URL.");
    return;
  }

  try {
    const response = await fetch(`/api/events/${encodeURIComponent(eventId)}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(payload?.error || `HTTP ${response.status}`);
    }
    renderDetail(payload);
    els.detailContent.classList.remove("hidden");
  } catch (error) {
    showError(error.message || "Detail kejadian gagal dimuat.");
    return;
  } finally {
    els.detailLoading.classList.add("hidden");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  setupNavigation();
  loadDetail();
});
