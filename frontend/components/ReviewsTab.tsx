"use client";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

function Stars({ v, onPick }: { v: number; onPick?: (n: number) => void }) {
  return (
    <span className={onPick ? "cursor-pointer text-[18px]" : "text-warn"}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} onClick={onPick ? () => onPick(n) : undefined}
          className={n <= Math.round(v) ? "text-warn" : "text-line"}>★</span>
      ))}
    </span>
  );
}

export default function ReviewsTab({ agentId, authed }: { agentId: string; authed: boolean }) {
  const [data, setData] = useState<{ reviews: any[]; my_review: any; rating_avg: number; rating_count: number } | null>(null);
  const [rating, setRating] = useState(0);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const load = () => api.reviews(agentId).then((d) => {
    setData(d);
    if (d.my_review) { setRating(d.my_review.rating); setText(d.my_review.review_text || ""); }
  }).catch(() => {});
  useEffect(() => { load(); }, [agentId]);

  async function submit() {
    if (rating < 1) { setErr("Pick a star rating."); return; }
    setBusy(true); setErr("");
    try { await api.writeReview(agentId, { rating, text: text || undefined }); await load(); }
    catch (e: any) { setErr(e.status === 401 ? "Sign in with Nyquest to review." : e.status === 403 ? "A Nyquest Pro account is required to review." : e.message); }
    finally { setBusy(false); }
  }

  if (!data) return <div className="py-8 text-center text-[13px] text-faint">Loading reviews…</div>;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        {data.rating_count > 0 ? (
          <><Stars v={data.rating_avg} /><span className="text-[15px] font-semibold text-ink">{data.rating_avg.toFixed(1)}</span>
            <span className="text-[12px] text-faint">· {data.rating_count} review{data.rating_count === 1 ? "" : "s"}</span></>
        ) : <span className="text-[13px] text-dim">No reviews yet — be the first.</span>}
      </div>

      {authed ? (
        <div className="rounded-xl border border-line bg-panel2 p-4">
          <div className="mb-2 text-[12px] font-medium text-dim">{data.my_review ? "Update your review" : "Write a review"}</div>
          <Stars v={rating} onPick={setRating} />
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} placeholder="What worked, what didn't? (optional)"
            className="mt-2 w-full rounded-lg border border-line bg-panel px-3 py-2 text-[13px] text-ink outline-none focus:border-vi/60" />
          {err && <p className="mt-1 text-[12px] text-bad">{err}</p>}
          <button onClick={submit} disabled={busy} className="mt-2 rounded-lg bg-vi px-4 py-2 text-[13px] font-semibold text-white hover:opacity-90 disabled:opacity-50">{busy ? "Saving…" : data.my_review ? "Update review" : "Submit review"}</button>
        </div>
      ) : <div className="rounded-xl border border-dashed border-line p-4 text-[13px] text-faint">Sign in with Nyquest to leave a review.</div>}

      <div className="space-y-2">
        {data.reviews.map((r, i) => (
          <div key={i} className="rounded-xl border border-line bg-panel p-3">
            <div className="flex items-center gap-2">
              <Stars v={r.rating} />
              <span className="text-[12px] font-medium text-ink">{r.reviewer}</span>
              {r.verified_install && <span className="rounded-full border border-ok/40 bg-ok/10 px-1.5 py-0.5 text-[10px] text-ok">verified install</span>}
            </div>
            {r.review_text && <p className="mt-1 text-[12.5px] text-dim">{r.review_text}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
