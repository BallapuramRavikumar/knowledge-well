// renderer.gemini.js
// Registers a renderer for Google Gemini style answers
(function () {
  function textNode(s) { return document.createTextNode(String(s || "")); }
  function chip(txt, cls = "source") { const span=document.createElement("span"); span.className=cls; span.appendChild(textNode(txt)); return span; }
  function parseSources(s) {
    const refs = [];
    const cleaned = s.replace(/\[(.*?)\]/g, (_, r) => { refs.push(r); return ""; }).trim();
    return { text: cleaned, refs };
  }

  function renderAnswer(raw) {
    const t = String(raw || "").replace(/\r/g, "");
    const frag = document.createDocumentFragment();

    // Sections are usually **Challenges:** and **Solutions...:**
    const secRe = /(?:^|\n)\s*\*{0,3}[^*\n]*\b(challenges?|problems?)\b[^*\n]*\*{0,3}\s*:\s*([\s\S]*?)(?=(?:^|\n)\s*\*{0,3}[^*\n]*solutions?[^*\n]*\*{0,3}\s*:|$)/i;   
    const m = t.match(secRe);
    const solutionsHeaderRe = /(?:^|\n)\s*\*{0,3}[^*\n]*solutions?[^*\n]*\*{0,3}\s*:\s*/i;
    let leadText = "", challText = "", solText = "";

    if (!m) {
    // Try a generic split on the Solutions header and continue rendering
    const parts = t.split(solutionsHeaderRe);
    challText = (parts[0] || t).trim();
    solText   = (parts[1] || "").trim();
    } else {
    leadText  = t.slice(0, m.index).trim();
    challText = (m[2] || "").trim();
    const solMatch = t.slice(m.index + m[0].length).match(solutionsHeaderRe);
    solText   = solMatch ? t.slice(m.index + m[0].length + solMatch[0].length).trim() : "";
    }

    // (keep the rest of the function the same, using leadText/challText/solText)


    leadText = t.slice(0, m.index).trim();
    challText = (m[2] || "").trim();
    const solMatch = t.slice(m.index + m[0].length).match(solutionsHeaderRe);
    solText = solMatch ? t.slice(m.index + m[0].length + solMatch[0].length).trim() : "";

    if (leadText) { const lead = document.createElement("div"); lead.className = "answer-lead"; lead.appendChild(textNode(leadText)); frag.appendChild(lead); }

    // Parse bullet challenges (* / - / •)
    const challItems = [...challText.matchAll(/(?:^|\n)[-\u2022*]\s+(.*?)(?=\n[-\u2022*]|\n*$)/g)].map(x => x[1].trim());
    if (challItems.length) {
      const block = document.createElement("div"); block.className = "answer-block";
      challItems.forEach((it, i) => {
        // Try to split **Title**: rest  OR Title: rest
        let title = null, rest = it;
        const bold = it.match(/\*\*(.*?)\*\*\s*:?\s*(.*)/);
        if (bold) { title = bold[1].trim(); rest = bold[2].trim(); }
        else { const c = it.indexOf(":"); if (c > 0) { title = it.slice(0, c).trim(); rest = it.slice(c + 1).trim(); } }
        const { text, refs } = parseSources(rest);
        const card = document.createElement("div"); card.className="answer-card";
        const h4 = document.createElement("h4");
        const idx = document.createElement("span"); idx.className="idx"; idx.appendChild(textNode(String(i+1)));
        h4.appendChild(idx); h4.appendChild(textNode(" " + (title || ("Item " + (i+1)))));
        card.appendChild(h4);
        if (text) { const p = document.createElement("p"); p.appendChild(textNode(text)); card.appendChild(p); }
        if (refs.length) { const row=document.createElement("div"); row.className="sources"; refs.slice(0,6).forEach(r=>row.appendChild(chip(r))); card.appendChild(row); }
        block.appendChild(card);
      });
      frag.appendChild(block);
    }

    // Solutions: usually bullet list
    if (solText) {
      const bullets = [...solText.matchAll(/(?:^|\n)[-\u2022*]\s+(.*?)(?=\n[-\u2022*]|\n*$)/g)].map(m => m[1].trim());
      const numbered = [...solText.matchAll(/(?:^|\n)\s*\d+\.\s+([\s\S]*?)(?=\n\s*\d+\.|\n*$)/g)].map(m => m[1].trim());
      const items = bullets.length ? bullets : numbered;

      const sc = document.createElement("div"); sc.className = "solutions-card";
      const h = document.createElement("h4"); h.appendChild(textNode("Solutions")); sc.appendChild(h);

      if (items.length) {
        const ul = document.createElement("ul"); ul.className = "solutions-list";
        items.forEach(it => {
          const { text, refs } = parseSources(it);
          const li = document.createElement("li"); li.appendChild(textNode(text));
          if (refs.length) { const row=document.createElement("div"); row.className="sources"; refs.forEach(r=>row.appendChild(chip(r))); li.appendChild(row); }
          ul.appendChild(li);
        });
        sc.appendChild(ul);
      } else {
        const p = document.createElement("p"); p.appendChild(textNode(solText)); sc.appendChild(p);
      }
      frag.appendChild(sc);
    }

    if (!frag.textContent.trim()) {
      const p = document.createElement("p"); p.appendChild(textNode(t.trim() || "—"));
      frag.appendChild(p);
    }
    return frag;
  }

  // ---- Graph summary (same as GPT-4o file for consistency) ----
  function _normSig(s){ return String(s||'').toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim(); }
  function _similar(a,b){
    const A=new Set(_normSig(a).split(' ')), B=new Set(_normSig(b).split(' ')); if(!A.size||!B.size) return false;
    let inter=0; A.forEach(t=>{ if(B.has(t)) inter++; }); const j=inter/Math.max(1, A.size+B.size-inter); return j>0.85;
  }
  function uniqBySimilarity(list){ const out=[]; list.forEach(x=>{ if(x && !out.some(y=>y===x||_similar(x,y))) out.push(x); }); return out; }
  function chip2(txt, cls){ return chip(txt, cls); }

  function renderGraphSummary(raw){
    const text = String(raw||'').replace(/\r/g,'');
    const items = [];
    const re = /Keyword\s*:\s*([^\-\n]+)?(?:\s*-\s*Paper\s*:\s*([^\n•]+))?([\s\S]*?)(?=Keyword\s*:|$)/gi;
    let m; while ((m = re.exec(text)) !== null){
      const keyword=(m[1]||'').trim(), paper=(m[2]||'').trim(), tail=(m[3]||'').trim();
      let frags = tail.includes('•') ? tail.split('•') : tail.split(/\n+/);
      frags = frags.map(s=>s.replace(/^(?:Content|Summary|Abstract(?:\s*Content)?)\s*:\s*/i,'').replace(/^[—-]\s*/,'').trim()).filter(Boolean);
      frags = uniqBySimilarity(frags);
      if (keyword || paper || frags.length) items.push({keyword, paper, abstracts: frags});
    }
    const wrap = document.createElement('div'); wrap.className='graph-grid';
    if (!items.length){
      uniqBySimilarity(text.split(/\n\n+|•/g).map(s=>s.trim()).filter(Boolean)).slice(0,8)
        .forEach(c=>{ const card=document.createElement('div'); card.className='gcard'; card.appendChild(textNode(c)); wrap.appendChild(card); });
      return wrap;
    }
    items.slice(0,12).forEach(it=>{
      const card=document.createElement('div'); card.className='gcard';
      const meta=document.createElement('div'); meta.className='meta';
      if (it.keyword) meta.appendChild(chip2(it.keyword,'kbadge'));
      if (it.paper) meta.appendChild(chip2(it.paper,'pbadge'));
      card.appendChild(meta);
      const list = uniqBySimilarity(it.abstracts||[]);
      if (list.length){
        const ul=document.createElement('ul'); ul.className='abstr';
        const MAX=5; list.slice(0,MAX).forEach(a=>{ const li=document.createElement('li'); li.appendChild(textNode(a)); ul.appendChild(li); });
        card.appendChild(ul);
        if (list.length>MAX){
          const hidden=document.createElement('ul'); hidden.className='abstr'; hidden.style.display='none';
          list.slice(MAX).forEach(a=>{ const li=document.createElement('li'); li.appendChild(textNode(a)); hidden.appendChild(li); });
          card.appendChild(hidden);
          const more=document.createElement('button'); more.className='btn btn-secondary more'; more.appendChild(textNode('Show more'));
          more.addEventListener('click',()=>{ const open=hidden.style.display!=='none'; hidden.style.display=open?'none':''; more.textContent=open?'Show more':'Show less'; });
          card.appendChild(more);
        }
      }
      wrap.appendChild(card);
    });
    return wrap;
  }

  const renderer = {
    name: "gemini-2.5-pro",
    matches(meta) {
      const p = (meta?.provider || "").toUpperCase();
      const m = (meta?.model || "").toLowerCase();
      return p.includes("GOOGLE") || p.includes("GEMINI") || m.includes("gemini");
    },
    renderAnswer,
    renderGraphSummary,
  };

  window.LLM_RENDERERS = window.LLM_RENDERERS || [];
  window.LLM_RENDERERS.push(renderer);

  if (!window.getRendererFor) {
    window.getRendererFor = function(meta){
      for (const r of window.LLM_RENDERERS) { try { if (r.matches(meta)) return r; } catch {} }
      return window.LLM_RENDERERS[0] || null;
    };
  }
})();
