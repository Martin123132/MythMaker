let appState = null;
let currentScene = null;

const el = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!data.ok) {
    throw new Error(data.error || "MythMaker request failed");
  }
  return data;
}

function lineId(prefix, text, index) {
  return `${prefix}_${index}_${text.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "item"}`;
}

function renderStateToEditors() {
  el("charactersText").value = (appState.characters || [])
    .map((item) => `${item.name || ""} | ${item.role || ""} | ${item.creed || ""} | ${(item.phrases || [])[0] || ""}`)
    .join("\n");
  el("placesText").value = (appState.places || [])
    .map((item) => `${item.name || ""} | ${item.texture || ""} | ${(item.rules || [])[0] || ""}`)
    .join("\n");
  el("phrasesText").value = (appState.phrases || []).join("\n");
  el("relicsText").value = (appState.relics || [])
    .map((item) => `${item.name || ""} | ${item.power || ""}`)
    .join("\n");
  el("rulesText").value = (appState.rules || [])
    .map((item) => `${item.name || ""} | ${item.text || ""}`)
    .join("\n");
}

function parseEditorsToState() {
  const parseLines = (text) => text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const split = (line) => line.split("|").map((part) => part.trim());
  const characters = parseLines(el("charactersText").value).map((line, index) => {
    const [name, role, creed, phrase] = split(line);
    return {
      id: lineId("char", name || "character", index),
      name: name || `Character ${index + 1}`,
      role: role || "unassigned myth participant",
      glyph: (name || "?").trim().slice(0, 1).toUpperCase(),
      creed: creed || "The room knows more than it admits",
      voice: role || "available for nonsense",
      phrases: [phrase || "I was not briefed on becoming mythological."],
    };
  });
  const places = parseLines(el("placesText").value).map((line, index) => {
    const [name, texture, rule] = split(line);
    return {
      id: lineId("place", name || "place", index),
      name: name || `Place ${index + 1}`,
      texture: texture || "a room with strong opinions",
      rules: [rule || "If it moves, it becomes lore."],
    };
  });
  const relics = parseLines(el("relicsText").value).map((line, index) => {
    const [name, power] = split(line);
    return {
      id: lineId("relic", name || "relic", index),
      name: name || `Relic ${index + 1}`,
      power: power || "makes the scene slightly worse",
    };
  });
  const rules = parseLines(el("rulesText").value).map((line, index) => {
    const [name, text] = split(line);
    return {
      id: lineId("rule", name || "rule", index),
      name: name || `Rule ${index + 1}`,
      text: text || "No myth may leave unchanged.",
    };
  });

  return {
    ...appState,
    characters,
    places,
    phrases: parseLines(el("phrasesText").value),
    relics,
    rules,
  };
}

async function loadState() {
  const data = await api("/api/state");
  appState = data.state;
  renderStateToEditors();
}

async function loadDoctor() {
  try {
    const data = await api("/api/doctor");
    const doctor = data.doctor;
    el("doctorStatus").textContent = `Local only - ${doctor.character_count} characters`;
  } catch {
    el("doctorStatus").textContent = "Local only";
  }
}

async function generateScene(useSameSeed = false) {
  const payload = {
    mode: el("modeSelect").value,
    weirdness: Number(el("weirdnessInput").value),
    cast_size: Number(el("castSizeInput").value),
  };
  const lockedSeed = el("lockSeedInput").checked ? el("seedInput").value.trim() : "";
  if (useSameSeed && currentScene) {
    payload.seed = currentScene.seed;
  } else if (lockedSeed) {
    payload.seed = lockedSeed;
  }

  const data = await api("/api/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  currentScene = data.scene;
  if (!el("lockSeedInput").checked) {
    el("seedInput").value = currentScene.seed;
  }
  renderScene(currentScene);
  setMessage("Scene generated.");
}

function renderScene(scene) {
  el("sceneTitle").textContent = scene.title;
  el("sceneMeta").textContent = `${scene.setting} | ${scene.mode} | seed ${scene.seed}`;
  el("scriptOutput").textContent = scene.script;
  renderTrace(scene);
}

function renderTrace(scene) {
  const cards = [];
  cards.push(`
    <div class="trace-card">
      <strong>${escapeHtml(scene.collision.kind)}</strong>
      <code>${escapeHtml(scene.collision.action)}
midpoint=${escapeHtml(String(scene.collision.midpoint))}
rule=${escapeHtml(scene.collision.rule)}</code>
    </div>
  `);
  for (const item of scene.cast || []) {
    cards.push(`
      <div class="trace-card">
        <strong>${escapeHtml(item.name)} - ${escapeHtml(item.signature)}</strong>
        <code>trace ${escapeHtml(JSON.stringify(item.trace))}
mood=${escapeHtml(item.mood)}
drift=${escapeHtml(item.drift_type)}
creed=${escapeHtml(item.drifted_creed)}</code>
      </div>
    `);
  }
  el("traceOutput").innerHTML = cards.join("");
}

async function saveSeeds() {
  appState = parseEditorsToState();
  const data = await api("/api/state", {
    method: "POST",
    body: JSON.stringify({ state: appState }),
  });
  appState = data.state;
  renderStateToEditors();
  setMessage("Seed bank saved.");
  await loadDoctor();
}

async function resetSeeds() {
  const data = await api("/api/state", {
    method: "POST",
    body: JSON.stringify({ reset: true }),
  });
  appState = data.state;
  renderStateToEditors();
  setMessage("Bottom House restored.");
  await loadDoctor();
}

async function saveFavourite() {
  if (!currentScene) {
    setMessage("Generate a scene first.");
    return;
  }
  await api("/api/favourites", {
    method: "POST",
    body: JSON.stringify({ scene: currentScene }),
  });
  setMessage("Favourite saved.");
  await loadFavourites();
}

async function loadFavourites() {
  const data = await api("/api/favourites");
  const favourites = data.favourites || [];
  if (!favourites.length) {
    el("favouritesList").innerHTML = "<p>No saved favourites yet.</p>";
    return;
  }
  el("favouritesList").innerHTML = favourites
    .map((item) => `
      <article class="favourite-card">
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.mode || "")} | seed ${escapeHtml(String(item.seed || ""))}</p>
        <button data-load-favourite="${escapeHtml(item.id)}">Load</button>
      </article>
    `)
    .join("");
  for (const button of document.querySelectorAll("[data-load-favourite]")) {
    button.addEventListener("click", () => {
      const favourite = favourites.find((item) => item.id === button.dataset.loadFavourite);
      if (favourite && favourite.scene) {
        currentScene = favourite.scene;
        renderScene(currentScene);
        el("seedInput").value = currentScene.seed || "";
        setMessage("Favourite loaded.");
      }
    });
  }
}

async function copyScript() {
  if (!currentScene) {
    setMessage("Generate a scene first.");
    return;
  }
  await navigator.clipboard.writeText(currentScene.script);
  setMessage("Script copied.");
}

async function exportScene(format) {
  if (!currentScene) {
    setMessage("Generate a scene first.");
    return;
  }
  const data = await api("/api/export", {
    method: "POST",
    body: JSON.stringify({ scene: currentScene, format }),
  });
  setMessage(`Exported ${data.export.format.toUpperCase()}: ${data.export.path}`);
}

function switchTab(tabName) {
  for (const tab of document.querySelectorAll(".tab")) {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  }
  for (const editor of document.querySelectorAll(".editor")) {
    editor.classList.remove("active");
  }
  el(`${tabName}Editor`).classList.add("active");
}

function setMessage(message) {
  el("actionMessage").textContent = message;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function bindEvents() {
  el("generateButton").addEventListener("click", () => generateScene(false).catch((err) => setMessage(err.message)));
  el("sameSeedButton").addEventListener("click", () => generateScene(true).catch((err) => setMessage(err.message)));
  el("saveSeedsButton").addEventListener("click", () => saveSeeds().catch((err) => setMessage(err.message)));
  el("resetButton").addEventListener("click", () => resetSeeds().catch((err) => setMessage(err.message)));
  el("saveButton").addEventListener("click", () => saveFavourite().catch((err) => setMessage(err.message)));
  el("copyButton").addEventListener("click", () => copyScript().catch((err) => setMessage(err.message)));
  el("exportTxtButton").addEventListener("click", () => exportScene("txt").catch((err) => setMessage(err.message)));
  el("exportHtmlButton").addEventListener("click", () => exportScene("html").catch((err) => setMessage(err.message)));
  el("weirdnessInput").addEventListener("input", () => {
    el("weirdnessValue").textContent = el("weirdnessInput").value;
  });
  for (const tab of document.querySelectorAll(".tab")) {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  }
}

async function init() {
  bindEvents();
  await loadState();
  await loadFavourites();
  await loadDoctor();
}

init().catch((err) => setMessage(err.message));
