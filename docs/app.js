(() => {
  const $ = (id) => document.getElementById(id);

  const state = {
    catalog: null,
    category: "all",
    query: "",
    deferredPrompt: null,
  };

  function toast(msg) {
    const el = $("toast");
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.remove("show"), 1600);
  }

  function normalize(s) {
    return (s || "").toLowerCase();
  }

  /** Lightweight fuzzy score: subsequence match + token bonuses. Higher is better. */
  function scoreItem(item, query) {
    if (!query) return 1;
    const q = normalize(query).trim();
    if (!q) return 1;
    const hay = normalize(
      [item.title, item.command, item.description, ...(item.tags || []), item.category, item.source]
        .join(" ")
    );
    if (hay.includes(q)) return 100 + (hay.startsWith(q) ? 20 : 0);

    // token AND
    const tokens = q.split(/\s+/).filter(Boolean);
    let tokenHits = 0;
    for (const t of tokens) {
      if (hay.includes(t)) tokenHits += 1;
    }
    if (tokenHits === tokens.length && tokens.length) return 60 + tokenHits * 5;

    // subsequence fuzzy on title+command
    const compact = normalize(item.title + " " + item.command);
    let qi = 0;
    for (let i = 0; i < compact.length && qi < q.length; i++) {
      if (compact[i] === q[qi]) qi++;
    }
    if (qi === q.length) return 20 + Math.floor((q.length / compact.length) * 10);
    return 0;
  }

  function filtered() {
    if (!state.catalog) return [];
    const items = state.catalog.commands.filter((c) => {
      if (state.category !== "all" && c.category !== state.category) return false;
      return scoreItem(c, state.query) > 0;
    });
    items.sort((a, b) => scoreItem(b, state.query) - scoreItem(a, state.query));
    return items;
  }

  function categoryLabel(id) {
    const cat = (state.catalog.categories || []).find((c) => c.id === id);
    return cat ? cat.label : id;
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast("Copied to clipboard");
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      toast("Copied to clipboard");
    }
  }

  function renderFilters() {
    const box = $("filters");
    const cats = [{ id: "all", label: "All" }, ...(state.catalog.categories || [])];
    box.innerHTML = "";
    for (const cat of cats) {
      const count =
        cat.id === "all"
          ? state.catalog.commands.length
          : state.catalog.commands.filter((c) => c.category === cat.id).length;
      if (cat.id !== "all" && count === 0) continue;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip" + (state.category === cat.id ? " active" : "");
      btn.textContent = `${cat.label} (${count})`;
      btn.addEventListener("click", () => {
        state.category = cat.id;
        render();
      });
      box.appendChild(btn);
    }
  }

  function renderResults() {
    const items = filtered();
    $("count").textContent = `${items.length} command${items.length === 1 ? "" : "s"}`;
    const root = $("results");
    root.innerHTML = "";
    if (!items.length) {
      root.innerHTML = `<div class="empty">No commands match. Try another search or category.</div>`;
      return;
    }
    const frag = document.createDocumentFragment();
    for (const item of items) {
      const card = document.createElement("article");
      card.className = "card";
      card.dataset.id = item.id;

      const badges = [];
      badges.push(
        `<span class="badge${item.source === "toolkit" ? " toolkit" : ""}">${
          item.source === "toolkit" ? "toolkit" : "adb"
        }</span>`
      );
      badges.push(`<span class="badge">${categoryLabel(item.category)}</span>`);
      if (item.risk === "caution") badges.push(`<span class="badge caution">caution</span>`);

      const examples =
        item.examples && item.examples.length
          ? `<div class="examples"><strong>Examples:</strong> ${item.examples
              .map((e) => `<div><code>${escapeHtml(e)}</code></div>`)
              .join("")}</div>`
          : "";

      const tags =
        item.tags && item.tags.length
          ? `<div class="tags">${item.tags
              .slice(0, 8)
              .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
              .join("")}</div>`
          : "";

      card.innerHTML = `
        <div class="card-head">
          <h2>${escapeHtml(item.title)}</h2>
          <div>${badges.join(" ")}</div>
        </div>
        <p class="desc">${escapeHtml(item.description || "")}</p>
        <div class="cmd">
          <pre></pre>
          <button type="button" class="btn secondary copy">Copy</button>
        </div>
        ${examples}
        ${tags}
      `;
      card.querySelector("pre").textContent = item.command;
      card.querySelector(".copy").addEventListener("click", () => copyText(item.command));
      frag.appendChild(card);
    }
    root.appendChild(frag);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function render() {
    renderFilters();
    renderResults();
  }

  function initTheme() {
    const saved = localStorage.getItem("adb-finder-theme");
    const theme = saved || "dark";
    document.documentElement.setAttribute("data-theme", theme);
    $("themeBtn").addEventListener("click", () => {
      const next =
        document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("adb-finder-theme", next);
      // Keep manifest theme roughly in sync for installed PWA chrome
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.content = next === "dark" ? "#0d1117" : "#f6f8fa";
    });
  }

  function initInstall() {
    const btn = $("installBtn");
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      state.deferredPrompt = e;
      btn.hidden = false;
    });
    btn.addEventListener("click", async () => {
      if (!state.deferredPrompt) return;
      state.deferredPrompt.prompt();
      await state.deferredPrompt.userChoice;
      state.deferredPrompt = null;
      btn.hidden = true;
    });
    window.addEventListener("appinstalled", () => {
      btn.hidden = true;
      toast("App installed");
    });
  }

  function registerSW() {
    if (!("serviceWorker" in navigator)) {
      $("swStatus").textContent = "Offline: unsupported";
      return;
    }
    const swUrl = new URL("sw.js", window.location.href).pathname;
    navigator.serviceWorker
      .register(swUrl, { scope: new URL("./", window.location.href).pathname })
      .then(() => {
        $("swStatus").textContent = "Offline ready";
      })
      .catch(() => {
        $("swStatus").textContent = "Offline: failed";
      });
  }

  async function loadCatalog() {
    const res = await fetch(new URL("commands.json", window.location.href), {
      cache: "no-cache",
    });
    if (!res.ok) throw new Error("Failed to load commands.json");
    state.catalog = await res.json();
    $("catalogMeta").textContent = `v${state.catalog.version || "?"} · ${
      state.catalog.commands.length
    } commands`;
    render();
  }

  function initSearch() {
    const input = $("search");
    let t = null;
    input.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        state.query = input.value;
        renderResults();
        renderFilters();
      }, 80);
    });
    // Focus shortcut
    window.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement !== input) {
        e.preventDefault();
        input.focus();
      }
    });
  }

  initTheme();
  initInstall();
  initSearch();
  registerSW();
  loadCatalog().catch((err) => {
    $("results").innerHTML = `<div class="empty">Could not load catalog: ${escapeHtml(
      err.message
    )}</div>`;
  });
})();
