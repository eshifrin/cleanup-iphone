const demoFixture = {
  meta: {
    generatedAt: "2026-03-27T00:00:00+00:00",
    grid: { columns: 4, rows: 6 },
    dockCapacity: 4,
    pageCapacity: 24
  },
  pages: [
    {
      id: "dock",
      name: "Dock",
      pageIndex: 0,
      capacity: 4,
      overflowCount: 0,
      slots: [
        { slotIndex: 0, item: { id: "app-phone", type: "app", name: "Phone" } },
        { slotIndex: 1, item: { id: "app-messages", type: "app", name: "Messages" } },
        { slotIndex: 2, item: { id: "app-camera", type: "app", name: "Camera" } },
        { slotIndex: 3, item: { id: "app-music", type: "app", name: "Music" } }
      ]
    },
    {
      id: "page-1",
      name: "Page 1",
      pageIndex: 1,
      capacity: 24,
      overflowCount: 0,
      slots: [
        { slotIndex: 0, item: { id: "app-mail", type: "app", name: "Mail" } },
        { slotIndex: 1, item: { id: "app-notion", type: "app", name: "Notion" } },
        {
          slotIndex: 2,
          item: {
            id: "folder-llm",
            type: "folder",
            name: "LLM",
            appCount: 4,
            apps: [
              { id: "app-chatgpt", type: "app", name: "ChatGPT" },
              { id: "app-claude", type: "app", name: "Claude" },
              { id: "app-gemini", type: "app", name: "Gemini" },
              { id: "app-perplexity", type: "app", name: "Perplexity" }
            ]
          }
        },
        { slotIndex: 3, item: { id: "app-calendar", type: "app", name: "Calendar" } },
        { slotIndex: 4, item: { id: "app-maps", type: "app", name: "Maps" } },
        { slotIndex: 5, item: { id: "app-photos", type: "app", name: "Photos" } },
        { slotIndex: 6, item: null },
        { slotIndex: 7, item: null },
        { slotIndex: 8, item: null },
        { slotIndex: 9, item: null },
        { slotIndex: 10, item: null },
        { slotIndex: 11, item: null },
        { slotIndex: 12, item: null },
        { slotIndex: 13, item: null },
        { slotIndex: 14, item: null },
        { slotIndex: 15, item: null },
        { slotIndex: 16, item: null },
        { slotIndex: 17, item: null },
        { slotIndex: 18, item: null },
        { slotIndex: 19, item: null },
        { slotIndex: 20, item: null },
        { slotIndex: 21, item: null },
        { slotIndex: 22, item: null },
        { slotIndex: 23, item: null }
      ]
    },
    {
      id: "page-2",
      name: "Page 2",
      pageIndex: 2,
      capacity: 24,
      overflowCount: 0,
      slots: Array.from({ length: 24 }, (_, slotIndex) => ({ slotIndex, item: null }))
    }
  ]
};

function clone(obj) {
  if (typeof structuredClone === "function") {
    return structuredClone(obj);
  }
  return JSON.parse(JSON.stringify(obj));
}

const state = {
  fixture: clone(demoFixture),
  baselineFixture: clone(demoFixture),
  draggedFrom: null
};

const planner = document.querySelector("#planner");
const fixtureInfo = document.querySelector("#fixture-info");
const loadDefaultBtn = document.querySelector("#load-default-btn");
const resetButton = document.querySelector("#reset-button");
const fixtureInput = document.querySelector("#fixture-input");

function prettyItem(item) {
  if (!item) {
    return "";
  }
  if (item.type === "folder") {
    return `${item.name} (${item.appCount} apps)`;
  }
  return item.name;
}

function createCardForItem(item) {
  const card = document.createElement("div");
  card.className = "drag-item";
  card.draggable = true;
  card.dataset.itemId = item.id;

  const title = document.createElement("div");
  title.className = "slot-title";
  title.textContent = item.name;
  card.appendChild(title);

  const type = document.createElement("div");
  type.className = "slot-meta";
  type.textContent = item.type === "folder" ? "Folder" : "App";
  card.appendChild(type);

  if (item.type === "folder") {
    const details = document.createElement("ul");
    details.className = "folder-apps";
    item.apps.slice(0, 4).forEach((app) => {
      const li = document.createElement("li");
      li.textContent = app.name;
      details.appendChild(li);
    });
    if (item.appCount > 4) {
      const li = document.createElement("li");
      li.textContent = `+${item.appCount - 4} more`;
      details.appendChild(li);
    }
    card.appendChild(details);
  }

  return card;
}

function locateSlot(pageId, slotIndex) {
  const page = state.fixture.pages.find((value) => value.id === pageId);
  if (!page) {
    return null;
  }
  return page.slots.find((slot) => slot.slotIndex === slotIndex) || null;
}

function onDragStart(event) {
  const card = event.currentTarget;
  const pageId = card.dataset.pageId;
  const slotIndex = Number(card.dataset.slotIndex);
  const slotData = locateSlot(pageId, slotIndex);

  if (!slotData || !slotData.item) {
    event.preventDefault();
    return;
  }

  state.draggedFrom = { pageId, slotIndex };
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", `${pageId}:${slotIndex}`);
}

function clearDragStyles() {
  document.querySelectorAll(".slot").forEach((slot) => {
    slot.classList.remove("over");
  });
}

function onDragOver(event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  event.currentTarget.classList.add("over");
}

function onDragLeave(event) {
  event.currentTarget.classList.remove("over");
}

function onDrop(event) {
  event.preventDefault();
  const target = event.currentTarget;
  target.classList.remove("over");

  if (!state.draggedFrom) {
    return;
  }

  const targetPageId = target.dataset.pageId;
  const targetSlotIndex = Number(target.dataset.slotIndex);

  const fromSlot = locateSlot(state.draggedFrom.pageId, state.draggedFrom.slotIndex);
  const toSlot = locateSlot(targetPageId, targetSlotIndex);

  if (!fromSlot || !fromSlot.item || !toSlot) {
    state.draggedFrom = null;
    return;
  }

  const tmp = toSlot.item;
  toSlot.item = fromSlot.item;
  fromSlot.item = tmp;
  state.draggedFrom = null;
  render();
}

function renderPage(page) {
  const section = document.createElement("article");
  section.className = "iphone-page";

  const header = document.createElement("header");
  const title = document.createElement("h3");
  title.textContent = page.name;
  const subtitle = document.createElement("span");
  subtitle.className = "meta";
  subtitle.textContent = `Capacity ${page.capacity} • Overflow ${page.overflowCount}`;
  header.appendChild(title);
  header.appendChild(subtitle);
  section.appendChild(header);

  const grid = document.createElement("div");
  grid.className = "slot-grid";

  page.slots.forEach((slot) => {
    const slotEl = document.createElement("div");
    slotEl.className = "slot";
    if (page.pageIndex === 0) {
      slotEl.classList.add("dock-slot");
    }
    slotEl.dataset.pageId = page.id;
    slotEl.dataset.slotIndex = String(slot.slotIndex);
    slotEl.draggable = false;

    if (slot.item) {
      const card = createCardForItem(slot.item);
      if (slot.item.type === "folder") {
        card.classList.add("folder");
      }
      card.dataset.pageId = page.id;
      card.dataset.slotIndex = String(slot.slotIndex);
      card.addEventListener("dragstart", onDragStart);
      card.addEventListener("dragend", clearDragStyles);
      slotEl.appendChild(card);
      slotEl.title = prettyItem(slot.item);
    } else {
      const placeholder = document.createElement("div");
      placeholder.className = "subtitle";
      placeholder.textContent = "Drop here";
      slotEl.appendChild(placeholder);
    }

    slotEl.addEventListener("dragover", onDragOver);
    slotEl.addEventListener("dragleave", onDragLeave);
    slotEl.addEventListener("drop", onDrop);

    grid.appendChild(slotEl);
  });

  section.appendChild(grid);
  const footer = document.createElement("div");
  footer.className = "page-footer";
  footer.textContent = `Page index ${page.pageIndex}`;
  section.appendChild(footer);
  return section;
}

function render() {
  planner.replaceChildren();
  state.fixture.pages.forEach((page) => {
    planner.appendChild(renderPage(page));
  });
  const generatedAt = state.fixture.meta?.generatedAt || "unknown time";
  fixtureInfo.textContent = `Fixture generated at ${generatedAt}`;
}

async function loadFixtureFromFile(file) {
  const text = await file.text();
  const parsed = JSON.parse(text);
  if (!parsed || !Array.isArray(parsed.pages)) {
    throw new Error("Fixture format is invalid. Expected { pages: [...] }.");
  }
  state.fixture = parsed;
  state.baselineFixture = clone(parsed);
  render();
}

loadDefaultBtn.addEventListener("click", () => {
  state.fixture = clone(demoFixture);
  state.baselineFixture = clone(demoFixture);
  render();
});

resetButton.addEventListener("click", () => {
  state.fixture = clone(state.baselineFixture);
  render();
});

fixtureInput.addEventListener("change", async () => {
  const [file] = fixtureInput.files;
  if (!file) {
    return;
  }
  try {
    await loadFixtureFromFile(file);
  } catch (error) {
    window.alert(`Could not load fixture: ${error.message}`);
  } finally {
    fixtureInput.value = "";
  }
});

render();
