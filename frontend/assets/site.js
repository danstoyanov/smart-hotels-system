const status = document.querySelector("#status");
const button = document.querySelector("#check");

async function checkConnection() {
  button.disabled = true;
  status.textContent = "Checking the connection…";
  try {
    const response = await fetch("/api/health", { signal: AbortSignal.timeout(7000), cache: "no-store" });
    const health = await response.json();
    if (!response.ok || health.status !== "ok") throw new Error("unavailable");
    status.textContent = "Connected. The website and database are ready.";
  } catch {
    status.textContent = "Connection unavailable. Please try again shortly.";
  } finally {
    button.disabled = false;
  }
}

async function loadSite() {
  try {
    const response = await fetch("/api/site", { signal: AbortSignal.timeout(7000) });
    if (!response.ok) return;
    const site = await response.json();
    document.querySelector("#hotel-name").textContent = site.name;
    document.querySelector("header a").textContent = site.name;
    document.querySelector("#timezone").textContent = site.timezone;
    document.documentElement.lang = site.language;
    document.title = `${site.name} · Demo`;
  } catch {
    // The static demo name remains visible when the API is unavailable.
  }
}

button.addEventListener("click", checkConnection);
loadSite();
checkConnection();
