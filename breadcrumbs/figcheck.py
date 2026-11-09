"""Automatic layout check for the report figures: every text label must sit inside the canvas and must not
overlap another label or a data mark (bars, scatter points, lines). Run after drawing.
Usage: uv run python -m breadcrumbs.figcheck
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PathCollection  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.text import Text  # noqa: E402

from . import figures as F  # noqa: E402

problems: list[str] = []
_orig_save = F.save


def check(fig, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    texts = [t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
    boxes = [(t, t.get_window_extent(r).expanded(1.02, 1.05)) for t in texts]
    for t, b in boxes:
        if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1:
            problems.append(f"{name}: text outside canvas: {t.get_text()[:40]!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (t1, b1), (t2, b2) = boxes[i], boxes[j]
            if b1.overlaps(b2):
                problems.append(f"{name}: text overlaps text: {t1.get_text()[:30]!r} / {t2.get_text()[:30]!r}")
    marks = []
    for ax in fig.axes:
        for p in ax.patches:
            if isinstance(p, Rectangle) and p.get_height() != 0 and p.get_facecolor()[3] > 0 and p.get_width() < 5:
                marks.append(("bar", p.get_window_extent(r)))
        for col in ax.collections:
            if isinstance(col, PathCollection):
                for off in col.get_offsets():
                    x, y = ax.transData.transform(off)
                    import matplotlib.transforms as mt
                    marks.append(("point", mt.Bbox.from_bounds(x - 3, y - 3, 6, 6)))
    for t, b in boxes:
        for kind, m in marks:
            if b.overlaps(m):
                problems.append(f"{name}: text over a {kind}: {t.get_text()[:40]!r}")
                break
    return _orig_save(fig, name)


F.save = check
F.main()
if problems:
    print("\n".join(sorted(set(problems))))
    raise SystemExit(f"{len(set(problems))} layout problems")
print("figcheck: no overlaps, nothing clipped")
