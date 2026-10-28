const $ = (selector) => document.querySelector(selector);
// Room photos come in two WebP widths; the browser picks one with srcset.
const images = {
  "manor-suite": "/assets/images/manor-suite",
  "garden-room": "/assets/images/garden-room",
};
// Only amenities with a matching local photograph get a photo card.
const amenityImages = { terrace: "/assets/images/manor-hero-900.webp" };
const iconPaths = {
  bed: "M3 18v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6M3 14h18M7 10V7.5A1.5 1.5 0 0 1 8.5 6h2A1.5 1.5 0 0 1 12 7.5V10M12 10V7.5A1.5 1.5 0 0 1 13.5 6h2A1.5 1.5 0 0 1 17 7.5V10M3 18v2M21 18v2",
  guests: "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM2.5 20a6.5 6.5 0 0 1 13 0M16 4.2a3.5 3.5 0 0 1 0 6.6M18 14a6.5 6.5 0 0 1 3.5 6",
  door: "M5 21V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v17M3 21h18M15 12h.01",
  wifi: "M2 9a15 15 0 0 1 20 0M5.5 12.5a10 10 0 0 1 13 0M9 16a5 5 0 0 1 6 0M12 19.5h.01",
  breakfast: "M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V9ZM17 10h1.5a2.5 2.5 0 0 1 0 5H17M8 3v3M12 3v3",
  terrace: "M12 21V11M12 11c-4 0-7-3-7-8 4 0 7 3 7 8ZM12 11c4 0 7-3 7-8-4 0-7 3-7 8ZM5 21h14",
  sparkle: "M12 3l2 6.5 6.5 2.5-6.5 2-2 7-2-7-6.5-2L10 9.5Z",
  arrival: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 7v5l3 2",
  pets: "M8 9.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM16 9.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM4.5 13.5a1.8 1.8 0 1 0 0-3.6 1.8 1.8 0 0 0 0 3.6ZM19.5 13.5a1.8 1.8 0 1 0 0-3.6 1.8 1.8 0 0 0 0 3.6ZM12 12c-3 0-5.5 3.5-5.5 6 0 1.5 1.2 2.5 2.7 2.5.9 0 1.8-.5 2.8-.5s1.9.5 2.8.5c1.5 0 2.7-1 2.7-2.5 0-2.5-2.5-6-5.5-6Z",
  family: "M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2.5 20v-2a5.5 5.5 0 0 1 11 0v2M17 11a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM15 20v-1.5a4 4 0 0 1 7 0V20",
  cancellation: "M4 6h16v14H4zM4 10h16M8 3v4M16 3v4M10 13l4 4M14 13l-4 4",
  prices: "M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9-9-9ZM7.5 7.5h.01",
  reservations: "M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3ZM9 12l2 2 4-4",
};
const state = { rooms: [], amenities: [], policies: [], search: null };

function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "icon");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", iconPaths[name] || iconPaths.sparkle);
  svg.append(path);
  return svg;
}
function iconItem(name, text) {
  const item = node("li");
  item.append(icon(name), node("span", "", text));
  return item;
}
function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}
function roomFeatures(room) {
  const list = node("ul", "feature-list");
  list.append(
    iconItem("door", plural(room.bedrooms, "bedroom")),
    iconItem("guests", `Sleeps ${room.capacity}`),
    iconItem("bed", room.beds.join(", ")),
  );
  return list;
}
function roomAmenities(room) {
  const list = node("ul", "chip-list");
  list.setAttribute("aria-label", "Included amenities");
  room.amenity_ids.forEach((id) => {
    const amenity = state.amenities.find((item) => item.id === id);
    if (amenity) list.append(iconItem(id, amenity.name));
  });
  return list;
}
function formatNight(night) {
  return new Date(`${night}T00:00:00`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
function stayText(checkIn, checkOut, guests) {
  const nights = Math.round(
    (new Date(`${checkOut}T00:00:00`) - new Date(`${checkIn}T00:00:00`)) / 86400000,
  );
  return `${formatNight(checkIn)} – ${formatNight(checkOut)} · ${plural(nights, "night")} · ${plural(Number(guests), "guest")}`;
}
function link(text, href, className = "") {
  const el = node("a", className, text);
  el.href = href;
  return el;
}
function image(room) {
  const el = document.createElement("img");
  const base = images[room.id];
  el.src = `${base}-1200.webp`;
  el.srcset = `${base}-640.webp 640w, ${base}-1200.webp 1200w`;
  el.sizes = "(max-width: 850px) 100vw, 50vw";
  el.alt = `Illustration of the fictional ${room.name} interior`;
  el.loading = "lazy";
  el.width = 960;
  el.height = 600;
  return el;
}
function details(room) {
  return `${room.bedrooms} bedroom${room.bedrooms === 1 ? "" : "s"} · Sleeps ${room.capacity} · ${room.beds.join(", ")}`;
}
function roomCard(room) {
  const card = node("article", "room-card");
  const photo = node("div", "room-photo");
  photo.append(image(room));
  photo.append(
    node("span", "photo-tag", "Fictional demo room"),
    node("span", "photo-badge", `Up to ${room.capacity} guests`),
  );
  const body = node("div", "room-body");
  body.append(
    node("h3", "", room.name),
    node("p", "", room.description),
    roomFeatures(room),
    roomAmenities(room),
  );
  const footer = node("div", "room-footer");
  footer.append(
    link(
      "View room →",
      `/rooms/${encodeURIComponent(room.id)}`,
      "button button-outline",
    ),
  );
  body.append(footer);
  card.append(photo, body);
  return card;
}
function amenityCard(item) {
  const photo = amenityImages[item.id];
  const card = node("article", photo ? "fact-card bento-photo" : "fact-card");
  if (photo) card.style.setProperty("--bento-image", `url("${photo}")`);
  const symbol = node("span", "fact-symbol");
  symbol.append(icon(item.id));
  const rooms = state.rooms
    .filter((room) => room.amenity_ids.includes(item.id))
    .map((room) => room.name);
  card.append(symbol, node("h3", "", item.name), node("p", "", item.description));
  if (rooms.length)
    card.append(node("p", "fact-rooms", `Included with: ${rooms.join(", ")}`));
  return card;
}
const demoPrefix = "Fictional demo policy.";
// Some policy clauses are notes for the concierge, not for guests. The hotel
// data keeps them; the website does not show them.
const assistantNote = /^(do not |this data reader )/i;
function guestText(sentence) {
  const clauses = sentence
    .replace(/\.$/, "")
    .split("; ")
    .filter((clause) => !assistantNote.test(clause));
  return clauses.length ? `${clauses.join("; ")}.` : "";
}
function policyCard(item) {
  const card = node("article", "policy-card");
  const head = node("div", "policy-head");
  const symbol = node("span", "fact-symbol");
  symbol.append(icon(item.id));
  const known = item.status !== "unknown";
  head.append(
    symbol,
    node("h3", "", item.title),
    node("span", known ? "policy-tag" : "policy-tag muted", known ? "Demo policy" : "Not set"),
  );
  // The tag shows the demo label, so the repeated prefix is not shown twice.
  const body = item.body.startsWith(demoPrefix)
    ? item.body.slice(demoPrefix.length).trim()
    : item.body;
  const points = body
    .split(/(?<=\.)\s+(?=[A-Z])/)
    .map(guestText)
    .filter(Boolean)
    .map((sentence) => node("li", "", sentence));
  // Long policies show two points first, so the section stays short on phones.
  const list = node("ul", "policy-points");
  list.append(...points.slice(0, 2));
  card.append(head, list);
  if (points.length > 2) {
    const more = node("details", "policy-more");
    const rest = node("ul", "policy-points");
    rest.append(...points.slice(2));
    more.append(node("summary", "", `Show all ${points.length} points`), rest);
    card.append(more);
  }
  return card;
}
function updateDepartureMin() {
  const arrival = $("#check-in");
  const date = new Date(`${arrival.value || arrival.min}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + 1);
  $("#check-out").min = date.toISOString().slice(0, 10);
}
function setupDateLimits(timezone) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const part = (type) => parts.find((item) => item.type === type).value;
  $("#check-in").min = `${part("year")}-${part("month")}-${part("day")}`;
  $("#check-in").addEventListener("change", updateDepartureMin);
  updateDepartureMin();
}
function renderInventory(nights) {
  const days = [...new Set((nights || []).map((item) => item.night))].sort();
  if (!days.length) return;
  const arrival = $("#check-in");
  if (days[0] > arrival.min) arrival.min = days[0];
  updateDepartureMin();
  const range = `${formatNight(days[0])} – ${formatNight(days.at(-1))}`;
  $("#inventory-note").textContent =
    `Sample nights: ${range}. A search does not hold a room.`;
  $("#footer-range").textContent = `Sample nights: ${range}`;
}
async function read(path) {
  const response = await fetch(path, {
    cache: "no-store",
    signal: AbortSignal.timeout(10000),
  });
  const data = await response.json();
  if (!response.ok || data.status === "unavailable")
    throw new Error(
      data.message || "Information unavailable. Try again shortly.",
    );
  return data;
}
// Errors on their own page offer the next step, so the guest is never stuck.
const searchAgain = ["Search available dates", "/#availability"];
function errorText(target, message, action) {
  const text = node("p", "notice error", message);
  if (!action) return target.replaceChildren(text);
  const box = node("div", "error-state");
  box.append(text, link(action[0], action[1], "button button-dark"));
  target.replaceChildren(box);
}
async function bookingRead(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    credentials: "same-origin",
    signal: AbortSignal.timeout(10000),
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.detail || "Demo reservation is unavailable.");
    error.status = response.status;
    throw error;
  }
  return data;
}
function renderBooking(target, booking) {
  const room = state.rooms.find((item) => item.id === booking.room_id);
  const card = node("div", "review-card confirmation-card");
  if (room) card.append(image(room));
  const text = node("div", "review-copy");
  // The reference is the one thing to keep, so it gets its own block.
  const reference = node("p", "booking-reference");
  reference.append(
    node("span", "booking-reference-label", "Reference: "),
    node("strong", "", booking.reference),
  );
  text.append(
    node("span", "eyebrow", "Demo reservation confirmed"),
    node("h2", "", room?.name || booking.room_id),
    node("p", "", stayText(booking.check_in, booking.check_out, booking.guests)),
    reference,
    node("p", "small-note", booking.message),
    link("Plan another stay", "/#availability", "button button-outline"),
  );
  card.append(text);
  target.replaceChildren(card);
  $("#review-page .back-link").hidden = true;
  $("#review-title").textContent = "Your demo reservation";
  $(".review-lead").textContent =
    "Keep the reference. You can open this demo reservation again in this browser.";
  markStepsDone();
}
const doneSteps = [
  "Every night of the stay was available.",
  "Your demo reservation is saved.",
  "Only this browser session can open it.",
];
function markStepsDone() {
  const steps = $(".review-steps");
  steps.classList.add("is-done");
  $("#steps-title").textContent = "Demo reservation saved";
  steps.querySelectorAll("li span").forEach((item, index) => {
    item.textContent = doneSteps[index];
  });
}
function renderCatalogue() {
  const list = $("#room-list");
  list.replaceChildren(...state.rooms.map(roomCard));
  if (!state.rooms.length) errorText(list, "No rooms are listed in this demo.");
  const amenities = $("#amenity-list");
  amenities.replaceChildren(...state.amenities.map(amenityCard));
  if (!state.amenities.length) errorText(amenities, "No amenities are listed.");
  const policies = $("#policy-list");
  policies.replaceChildren(...state.policies.map(policyCard));
  if (!state.policies.length)
    errorText(policies, "No stay information is listed.");
}
function roomDetail(room) {
  const target = $("#room-detail");
  target.replaceChildren();
  const layout = node("div", "detail-grid");
  const photo = node("div", "detail-photo");
  photo.append(image(room));
  const content = node("div", "detail-copy");
  const heading = node("h1", "", room.name);
  heading.id = "room-title";
  content.append(
    node("span", "eyebrow", "Fictional demo room"),
    heading,
    node("p", "lead", room.description),
    roomFeatures(room),
  );
  content.append(node("h2", "", "Included in this room"));
  const ul = node("ul", "detail-list");
  room.amenity_ids
    .map((id) => state.amenities.find((item) => item.id === id))
    .filter(Boolean)
    .forEach((amenity) => {
      const item = node("li");
      const text = node("div");
      text.append(node("strong", "", amenity.name), node("p", "", amenity.description));
      item.append(icon(amenity.id), text);
      ul.append(item);
    });
  content.append(ul);
  const plan = node("div", "plan-card");
  plan.append(
    node(
      "p",
      "small-note",
      "Search the sample nights to see which rooms are free for your stay.",
    ),
    link("Search available dates →", "/#availability", "button button-dark"),
  );
  content.append(plan);
  layout.append(photo, content);
  target.append(layout);
}
function searchQuery() {
  const params = new URLSearchParams({
    check_in: $("#check-in").value,
    check_out: $("#check-out").value,
    guests: $("#guests").value,
  });
  return params;
}
function reviewUrl(roomId, query) {
  const params = new URLSearchParams(query);
  params.set("room", roomId);
  return `/review?${params}`;
}
function renderResults(data, query) {
  const target = $("#availability-results");
  target.replaceChildren();
  const status = $("#availability-status");
  if (data.status === "unknown_inventory") {
    status.textContent =
      "Inventory is unknown for at least one suitable room on these dates. No room can be offered.";
    return;
  }
  if (data.status === "no_match" || !data.rooms.length) {
    const guests = Number(query.get("guests"));
    const capacity = Math.max(...state.rooms.map((room) => room.capacity));
    status.textContent = state.rooms.length && guests > capacity
      ? `No room holds ${guests} guests. The largest demo room sleeps ${capacity}.`
      : "No room is available for the full stay and guest count. Try other demo dates.";
    return;
  }
  status.textContent = `${data.rooms.length} room${data.rooms.length === 1 ? "" : "s"} available for the full demo stay. Search does not reserve a room.`;
  data.rooms.forEach((room) => {
    const card = node("article", "result-card");
    const photo = image(room);
    photo.sizes = "140px";
    const text = node("div", "result-copy");
    text.append(
      node("span", "result-tag", "Fictional demo room"),
      node("h3", "", room.name),
      node("p", "", details(room)),
      link(
        "Review this stay →",
        reviewUrl(room.id, query),
        "button button-dark",
      ),
    );
    card.append(photo, text);
    target.append(card);
  });
}
async function runSearch(event) {
  event.preventDefault();
  const form = $("#availability-form");
  if (!form.reportValidity()) return;
  const query = searchQuery();
  const status = $("#availability-status");
  const target = $("#availability-results");
  target.replaceChildren();
  status.textContent = "Checking the full demo stay…";
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const data = await read(`/api/availability?${query}`);
    if (data.status === "invalid_input")
      throw new Error(data.message || "Check the dates and guest count.");
    state.search = data;
    renderResults(data, query);
  } catch (error) {
    status.textContent =
      error.message || "Availability unavailable. Try again shortly.";
  } finally {
    button.disabled = false;
  }
}
async function renderReview() {
  const target = $("#review-detail");
  target.replaceChildren(
    node("p", "notice", "Checking this selection against the demo inventory…"),
  );
  const params = new URLSearchParams(location.search);
  const reference = params.get("reference");
  if (reference) {
    try {
      const booking = await bookingRead(
        `/api/bookings/${encodeURIComponent(reference)}`,
      );
      renderBooking(target, booking);
    } catch {
      errorText(target, "Demo reservation not found for this guest session.", searchAgain);
    }
    return;
  }
  const id = params.get("room");
  const checkIn = params.get("check_in");
  const checkOut = params.get("check_out");
  const guests = params.get("guests");
  if (!id || !checkIn || !checkOut || !guests) {
    errorText(
      target,
      "Choose dates and a room from the availability search first.",
      searchAgain,
    );
    return;
  }
  const query = new URLSearchParams({
    check_in: checkIn,
    check_out: checkOut,
    guests,
  });
  const storageKey = `demo-booking:${query.toString()}:${id}`;
  let pending;
  try {
    pending = JSON.parse(sessionStorage.getItem(storageKey) || "null");
  } catch {
    pending = null;
  }
  try {
    if (pending?.attempted && pending.request_id) {
      try {
        const booking = await bookingRead(
          `/api/bookings/by-request/${encodeURIComponent(pending.request_id)}`,
        );
        history.replaceState(null, "", `/review?reference=${encodeURIComponent(booking.reference)}`);
        renderBooking(target, booking);
        return;
      } catch (error) {
        if (error.status !== 404) throw error;
      }
    }
    const data = await read(`/api/availability?${query}`);
    const room = data.rooms?.find((item) => item.id === id);
    if (data.status !== "ok" || !room) {
      errorText(
        target,
        "This room is not available for the full stay. Please search again.",
        searchAgain,
      );
      return;
    }
    const card = node("div", "review-card");
    const photo = image(room);
    const text = node("div", "review-copy");
    text.append(
      node("span", "eyebrow", "Available in demo inventory"),
      node("h2", "", room.name),
    );
    text.append(node("p", "", stayText(checkIn, checkOut, guests)));
    const city = data.timezone.split("/").at(-1).replaceAll("_", " ");
    text.append(node("p", "", `Dates use hotel time (${city}).`));
    text.append(node("p", "small-note", "No price or currency is set."));
    const confirm = node("button", "button button-gold", "Confirm demo reservation");
    confirm.type = "button";
    const status = node("p", "notice", "Confirmation saves one demo reservation for this browser session.");
    status.setAttribute("role", "status");
    confirm.addEventListener("click", async () => {
      confirm.disabled = true;
      status.textContent = "Saving your demo reservation…";
      let requestId = pending?.request_id;
      if (!requestId) requestId = crypto.randomUUID();
      pending = { request_id: requestId, attempted: true };
      sessionStorage.setItem(storageKey, JSON.stringify(pending));
      try {
        await bookingRead("/api/session", { method: "POST" });
        const booking = await bookingRead("/api/bookings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: requestId,
            room_id: id,
            check_in: checkIn,
            check_out: checkOut,
            guests: Number(guests),
            confirmed: true,
          }),
        });
        history.replaceState(null, "", `/review?reference=${encodeURIComponent(booking.reference)}`);
        renderBooking(target, booking);
      } catch (error) {
        status.textContent =
          error.status === 409
            ? `${error.message} Search again, or reload to check this request.`
            : "The result is unclear. Reload this page or retry; the same request ID will be used.";
        confirm.disabled = false;
      }
    });
    // "← Change dates" above the heading is the one way back to search.
    text.append(confirm, status);
    card.append(photo, text);
    target.replaceChildren(card);
  } catch (error) {
    errorText(
      target,
      error.message || "Could not check availability. Try again.",
      searchAgain,
    );
  }
}
function renderRoute() {
  const path = location.pathname;
  $("#home-page").hidden = path !== "/";
  $("#room-page").hidden = !path.startsWith("/rooms/");
  $("#review-page").hidden = path !== "/review";
  if (path.startsWith("/rooms/")) {
    const id = decodeURIComponent(path.slice("/rooms/".length));
    const room = state.rooms.find((item) => item.id === id);
    if (room) roomDetail(room);
    else errorText($("#room-detail"), "This room is not part of the demo hotel.", ["See all rooms", "/#rooms"]);
  }
  if (path === "/review") renderReview();
}
// On phones the links sit behind a Menu button (shown by site.css only there).
function setupMenu() {
  const toggle = $("#nav-toggle");
  const shell = $(".nav-shell");
  const setOpen = (open) => {
    shell.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
  };
  toggle.addEventListener("click", () =>
    setOpen(!shell.classList.contains("is-open")),
  );
  $("#nav-links").addEventListener("click", (event) => {
    if (event.target.closest("a, button")) setOpen(false);
  });
  shell.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && shell.classList.contains("is-open")) {
      setOpen(false);
      toggle.focus();
    }
  });
}
async function init() {
  setupMenu();
  $("#availability-form").addEventListener("submit", runSearch);
  // Inventory only adds dates and counts; the page still works without it.
  const inventory = read("/api/hotel/inventory").catch(() => null);
  try {
    const [site, rooms, amenities, policies] = await Promise.all([
      read("/api/site"),
      read("/api/hotel/rooms"),
      read("/api/hotel/amenities"),
      read("/api/hotel/policies"),
    ]);
    state.rooms = rooms.data;
    state.amenities = amenities.data;
    state.policies = policies.data;
    $("#brand-name").textContent = site.name;
    $("#footer-name").textContent = site.name;
    $("#timezone").textContent = site.timezone;
    document.title = `${site.name} · Fictional demo`;
    document.documentElement.lang = site.language;
    setupDateLimits(site.timezone);
    renderCatalogue();
    renderInventory((await inventory)?.data);
  } catch {
    for (const selector of ["#room-list", "#amenity-list", "#policy-list"]) {
      errorText(
        $(selector),
        "Hotel information is unavailable. Reload the page to try again.",
      );
    }
  }
  renderRoute();
}
init();
