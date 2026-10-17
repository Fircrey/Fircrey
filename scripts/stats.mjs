// Genera <out>/stats-{dark,light}.svg a partir del calendario de contribuciones.
// Las cifras se componen con glifos ya convertidos a trazos (scripts/templates/stats.json),
// así que el resultado no depende de las fuentes instaladas en quien lo ve.
//
// Uso: GITHUB_TOKEN=... node scripts/stats.mjs [out]
import { mkdir, readFile, writeFile } from "node:fs/promises";

const USER = process.env.GITHUB_USER ?? "Fircrey";
const OUT = process.argv[2] ?? "dist";
const TEMPLATES = new URL("./templates/", import.meta.url);

const query = `query ($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}`;

async function fetchCalendar() {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      authorization: `bearer ${process.env.GITHUB_TOKEN}`,
      "content-type": "application/json",
      "user-agent": `${USER}-profile-stats`,
    },
    body: JSON.stringify({ query, variables: { login: USER } }),
  });
  if (!res.ok) throw new Error(`GraphQL respondió ${res.status}`);
  const { data, errors } = await res.json();
  if (errors) throw new Error(JSON.stringify(errors));
  return data.user.contributionsCollection.contributionCalendar;
}

function summarize(calendar) {
  const days = calendar.weeks.flatMap((w) => w.contributionDays);
  let longest = 0;
  let run = 0;
  for (const d of days) {
    run = d.contributionCount > 0 ? run + 1 : 0;
    longest = Math.max(longest, run);
  }
  const weekly = calendar.weeks.map((w) => w.contributionDays.reduce((s, d) => s + d.contributionCount, 0));
  const lastWeek = days.slice(-7).reduce((s, d) => s + d.contributionCount, 0);
  const bestWeek = Math.max(0, ...weekly);
  return {
    contributions: calendar.totalContributions,
    activeDays: days.filter((d) => d.contributionCount > 0).length,
    longestStreak: longest,
    bestWeek,
    lastWeek,
  };
}

// Ánimo del león marino según los datos reales de los últimos 7 días.
function mood({ lastWeek, bestWeek }) {
  if (lastWeek > 0 && lastWeek >= bestWeek * 0.6) return "happy"; // semana excepcional: juega con la pelota
  if (lastWeek > 0) return "clap"; // hubo actividad: aplaude
  return "blep"; // semana tranquila: saca la lengua
}

// Separador de miles con punto, también en cifras de 4 dígitos (Intl es-ES no lo pone).
const format = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");

function glyphRun(table, str, x, y, fill, track = 0) {
  let cx = x;
  const parts = [];
  for (const ch of str) {
    const g = table[ch];
    parts.push(`<path fill="${fill}" transform="translate(${cx.toFixed(1)} ${y})" d="${g.d}"/>`);
    cx += g.w + track;
  }
  return { svg: parts.join(""), width: cx - x - track };
}

function render(theme, meta, values, today) {
  return readFile(new URL(`stats-${theme}.svg`, TEMPLATES), "utf8").then((tpl) => {
    const colors = meta[theme];
    for (const slot of meta.slots) {
      const run = glyphRun(meta.glyphs, format(values[slot.key]), slot.x, slot.y, colors.text);
      tpl = tpl.replace(`<!--${slot.key}-->`, run.svg);
    }
    const u = meta.updated;
    const track = 0.08 * u.size;
    const dateWidth = [...today].reduce((s, ch) => s + meta.mono[ch].w, 0) + track * (today.length - 1);
    const start = u.x - meta.prefix_w - track - dateWidth;
    const prefix = u.prefix.replace('fill="#000"', `fill="${colors.muted}" transform="translate(${start.toFixed(1)} ${u.y})"`);
    const date = glyphRun(meta.mono, today, start + meta.prefix_w + track, u.y, colors.muted, track);
    tpl = tpl.replace("<!--updated-->", prefix + date.svg);
    const title =
      `Actividad en GitHub: ${format(values.contributions)} contribuciones en 12 meses, ` +
      `${values.activeDays} días con actividad, racha más larga de ${values.longestStreak} días, ` +
      `mejor semana con ${values.bestWeek} contribuciones. Actualizado ${today}.`;
    return tpl.replace("__TITLE__", title).replace("/*MOOD*/", `.mood-${mood(values)}{display:inline}`);
  });
}

const meta = JSON.parse(await readFile(new URL("stats.json", TEMPLATES), "utf8"));
const values = summarize(await fetchCalendar());
const today = new Date().toISOString().slice(0, 10);
await mkdir(OUT, { recursive: true });
for (const theme of ["dark", "light"]) {
  await writeFile(`${OUT}/stats-${theme}.svg`, await render(theme, meta, values, today));
}
console.log({ ...values, mood: mood(values) });
