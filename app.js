const state = {
	instances: [],
	search: "",
	network: "all",
	tag: null,
};

const cardsEl = document.getElementById("cards");
const countEl = document.getElementById("result-count");
const emptyEl = document.getElementById("empty");
const errorEl = document.getElementById("error");
const searchEl = document.getElementById("search");

// https://github.com/<org>/<repo>/blob/<sha>/<path>#Lx-Ly
const LINK_RE =
	/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/blob\/([0-9a-f]{40})\/([^#]+)(?:#(.+))?$/;

function parseLink(link) {
	const m = link.match(LINK_RE);
	if (!m) return null;
	const [, org, repo, sha, path, anchor] = m;
	return { org, repo, sha: sha.slice(0, 7), path, anchor: anchor || "" };
}

function el(tag, className, text) {
	const node = document.createElement(tag);
	if (className) node.className = className;
	if (text !== undefined) node.textContent = text;
	return node;
}

function render() {
	const q = state.search.toLowerCase();

	const visible = state.instances.filter((it) => {
		if (state.network !== "all" && it.network !== state.network) return false;
		if (state.tag && !(it.tags || []).includes(state.tag)) return false;
		if (!q) return true;
		const hay = [it.title, it.why, it.link, (it.tags || []).join(" ")]
			.join(" ")
			.toLowerCase();
		return q.split(/\s+/).every((word) => hay.includes(word));
	});

	cardsEl.innerHTML = "";
	for (const it of visible) cardsEl.appendChild(renderCard(it));

	emptyEl.classList.toggle("hidden", visible.length > 0 || !state.instances.length);
	countEl.textContent = state.instances.length
		? `${visible.length} of ${state.instances.length} examples`
		: "";
}

function renderCard(it) {
	const card = el("article", "card");
	const loc = parseLink(it.link);

	const title = el("h2", "card-title");
	const a = el("a");
	a.href = it.link;
	a.target = "_blank";
	a.rel = "noopener";
	a.textContent = it.title;
	title.appendChild(a);
	card.appendChild(title);

	card.appendChild(el("p", "card-why", it.why));

	if (it.tags?.length) {
		const tags = el("div", "card-tags");
		for (const t of it.tags) {
			const pill = el("button", "tag", t);
			if (state.tag === t) pill.classList.add("active");
			pill.addEventListener("click", () => {
				state.tag = state.tag === t ? null : t;
				render();
			});
			tags.appendChild(pill);
		}
		card.appendChild(tags);
	}

	const meta = el("div", "card-meta");
	meta.appendChild(el("span", "badge badge-network", it.network));
	if (it.verified_by_org)
		meta.appendChild(el("span", "badge badge-verified", `verified · ${it.verified_by_org}`));
	if (it.submitted_on) meta.appendChild(el("span", null, it.submitted_on));
	card.appendChild(meta);

	if (loc) {
		const row = el("div", "card-meta");
		const locEl = el("span", "card-loc");
		locEl.textContent = `${loc.org}/${loc.repo} · ${loc.path}${loc.anchor ? "#" + loc.anchor : ""} `;
		const sha = el("span", "sha", `@${loc.sha}`);
		locEl.appendChild(sha);
		row.appendChild(locEl);
		const view = el("a", "card-link", "View →");
		view.href = it.link;
		view.target = "_blank";
		view.rel = "noopener";
		row.appendChild(view);
		card.appendChild(row);
	}

	return card;
}

async function load() {
	try {
		const res = await fetch("cookbook.json");
		if (!res.ok) throw new Error(res.status);
		const data = await res.json();
		state.instances = (data.instances || []).slice().sort((a, b) =>
			(b.submitted_on || "").localeCompare(a.submitted_on || "")
		);
		render();
	} catch {
		errorEl.classList.remove("hidden");
	}
}

searchEl.addEventListener("input", (e) => {
	state.search = e.target.value.trim();
	render();
});

document.getElementById("network-filters").addEventListener("click", (e) => {
	const btn = e.target.closest(".chip");
	if (!btn) return;
	state.network = btn.dataset.network;
	for (const c of document.querySelectorAll("#network-filters .chip"))
		c.classList.toggle("active", c === btn);
	render();
});

// theme toggle
const root = document.documentElement;
const saved = localStorage.getItem("oc-theme");
if (saved) root.dataset.theme = saved;
else if (window.matchMedia("(prefers-color-scheme: light)").matches)
	root.dataset.theme = "light";

document.getElementById("theme-toggle").addEventListener("click", () => {
	root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
	localStorage.setItem("oc-theme", root.dataset.theme);
});

load();
