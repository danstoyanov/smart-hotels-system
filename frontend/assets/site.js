const $ = (selector) => document.querySelector(selector);
const images = {
  "manor-suite": "/assets/images/manor-suite.png",
  "garden-room": "/assets/images/garden-room.png",
};
const state = { rooms: [], amenities: [], policies: [], search: null };

function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function link(text, href, className = "") {
  const el = node("a", className, text);
  el.href = href;
  return el;
}
function image(room) {
  const el = document.createElement("img");
  el.src = images[room.id];
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
  photo.append(node("span", "photo-tag", "Fictional demo room"));
  const body = node("div", "room-body");
  body.append(
    node("h3", "", room.name),
    node("p", "", room.description),
    node("p", "room-meta", details(room)),
  );
  body.append(
    link(
      "View room →",
      `/rooms/${encodeURIComponent(room.id)}`,
      "button button-outline",
    ),
  );
  card.append(photo, body);
  return card;
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
function errorText(target, message) {
  target.replaceChildren(node("p", "notice error", message));
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
  text.append(
    node("span", "eyebrow", "Demo reservation confirmed"),
    node("h2", "", room?.name || booking.room_id),
    node("p", "", `${booking.check_in} to ${booking.check_out} · ${booking.guests} guests`),
    node("p", "booking-reference", `Reference: ${booking.reference}`),
    node("p", "small-note", booking.message),
    node("p", "small-note", "No price or payment is part of this demo."),
    link("Return to rooms", "/#rooms", "button button-outline"),
  );
  card.append(text);
  target.replaceChildren(card);
  $("#review-title").textContent = "Your demo reservation";
  $(".review-lead").textContent =
    "Your selected room is reserved in this fictional demo. This is not a real hotel booking.";
}
function renderCatalogue() {
  const list = $("#room-list");
  list.replaceChildren(...state.rooms.map(roomCard));
  if (!state.rooms.length) errorText(list, "No rooms are listed in this demo.");
  const amenities = $("#amenity-list");
  amenities.replaceChildren(
    ...state.amenities.map((item) => {
      const card = node("article", "fact-card");
      card.append(
        node("span", "fact-symbol", "✦"),
        node("h3", "", item.name),
        node("p", "", item.description),
      );
      return card;
    }),
  );
  if (!state.amenities.length) errorText(amenities, "No amenities are listed.");
  const policies = $("#policy-list");
  policies.replaceChildren(
    ...state.policies.map((item) => {
      const card = node("article", "policy-card");
      card.append(node("h3", "", item.title), node("p", "", item.body));
      return card;
    }),
  );
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
    node("p", "room-meta", details(room)),
  );
  const names = room.amenity_ids
    .map((id) => state.amenities.find((item) => item.id === id)?.name)
    .filter(Boolean);
  content.append(node("h2", "", "Included in this room"));
  const ul = node("ul", "detail-list");
  names.forEach((name) => ul.append(node("li", "", name)));
  content.append(ul);
  content.append(
    node(
      "p",
      "small-note",
      "Prices are not published. Search the sample dates to review available rooms.",
    ),
  );
  const choose = link(
    "Check dates for this room →",
    "/#availability",
    "button button-dark",
  );
  content.append(choose);
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
    status.textContent =
      "No room is available for the full stay and guest count. Try other demo dates.";
    return;
  }
  status.textContent = `${data.rooms.length} room${data.rooms.length === 1 ? "" : "s"} available for the full demo stay. Search does not reserve a room.`;
  data.rooms.forEach((room) => {
    const card = node("article", "result-card");
    card.append(node("h3", "", room.name), node("p", "", details(room)));
    card.append(
      link(
        "Review this stay →",
        reviewUrl(room.id, query),
        "button button-dark",
      ),
    );
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
      errorText(target, "Demo reservation not found for this guest session.");
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
    text.append(
      node(
        "p",
        "",
        `${checkIn} to ${checkOut} · ${data.nights} night${data.nights === 1 ? "" : "s"} · ${guests} guest${guests === "1" ? "" : "s"}`,
      ),
    );
    text.append(node("p", "", `Property timezone: ${data.timezone}`));
    text.append(
      node(
        "p",
        "small-note",
        "No price or currency is set. No room is held and no reservation is created.",
      ),
    );
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
    text.append(confirm, status);
    text.append(
      link("Choose different dates", "/#availability", "button button-outline"),
    );
    card.append(photo, text);
    target.replaceChildren(card);
  } catch (error) {
    errorText(
      target,
      error.message || "Could not check availability. Try again.",
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
    else errorText($("#room-detail"), "Room not found. Return to all rooms.");
  }
  if (path === "/review") renderReview();
}
async function init() {
  $("#availability-form").addEventListener("submit", runSearch);
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
    $("#timezone").textContent = site.timezone;
    document.title = `${site.name} · Fictional demo`;
    document.documentElement.lang = site.language;
    renderCatalogue();
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
