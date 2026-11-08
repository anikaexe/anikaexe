
import os
import json
import urllib.request
from pathlib import Path
from datetime import date, timedelta
from html import escape

USERNAME = os.environ.get("GITHUB_USERNAME", "anikaexe")
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {"login": USERNAME}
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "contribution-spectrum"
    },
    method="POST"
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)

if result.get("errors"):
    raise RuntimeError(result["errors"])

weeks = result["data"]["user"]["contributionsCollection"][
    "contributionCalendar"
]["weeks"]

counts = {
    day["date"]: day["contributionCount"]
    for week in weeks
    for day in week["contributionDays"]
}

# Last 90 days, including today
today = date.today()
days = [
    today - timedelta(days=i)
    for i in range(89, -1, -1)
]

values = [counts.get(day.isoformat(), 0) for day in days]
maximum = max(max(values), 1)

width = 960
height = 240
baseline = 185
left = 30
spacing = 10
bar_width = 6

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">',
    '<rect width="960" height="240" rx="14" fill="#080D16"/>',
    '<text x="30" y="34" fill="#A9CFFF" '
    'font-family="monospace" font-size="14" '
    'letter-spacing="2">CONTRIBUTION SPECTRUM</text>',
    '<text x="930" y="34" text-anchor="end" '
    'fill="#637C9D" font-family="monospace" '
    'font-size="11">LAST 90 DAYS</text>',
]

# Subtle horizontal guides
for y in (75, 115, 155, 185):
    parts.append(
        f'<line x1="30" y1="{y}" x2="930" y2="{y}" '
        'stroke="#22354D" stroke-width="1" '
        'stroke-dasharray="2 7"/>'
    )

# Each bar represents one day
for i, value in enumerate(values):
    x = left + i * spacing
    bar_height = 3 if value == 0 else 8 + (value / maximum) * 112
    y = baseline - bar_height

    color = (
        "#24374F" if value == 0
        else "#9BC9FF" if value >= maximum * 0.75
        else "#6AA8F5" if value >= maximum * 0.4
        else "#376FAF"
    )

    parts.append(
        f'<rect x="{x}" y="{y:.1f}" '
        f'width="{bar_width}" height="{bar_height:.1f}" '
        f'rx="2" fill="{color}">'
        f'<title>{escape(days[i].isoformat())}: '
        f'{value} contributions</title></rect>'
    )

parts.extend([
    '<text x="30" y="215" fill="#7890AE" '
    'font-family="monospace" font-size="11">90 DAYS AGO</text>',
    '<text x="930" y="215" text-anchor="end" '
    'fill="#7890AE" font-family="monospace" '
    'font-size="11">TODAY</text>',
    '</svg>'
])

output = Path("assests/contribution-spectrum.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(parts), encoding="utf-8")

print(f"Generated {output} with {sum(values)} contributions.")
