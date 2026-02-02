// renderer.gpt4o.js
// Registers a renderer for OPENAI GPT-4o style answers
(function () {
  function textNode(s) { return document.createTextNode(String(s || "")); }
  function chip(txt, cls = "source") {
    const span = document.createElement("span");
    span.className = cls;
    span.appendChild(textNode(txt));
    return span;
    }
  function parseSources(s) {
    const refs = [];
    const cleaned = s.replace(/\[(.*?)\]/g, (_, r) => { refs.push(r); return ""; }).trim();
    return { text: cleaned, refs };
  }
  function cardItem(idx, title, body, refs) {
    const wrap = document.createElement("div"); wrap.className = "answer-card";
    const h4 = document.createElement("h4");
    const bubble = document.createElement("span"); bubble.className = "idx"; bubble.appendChild(textNode(idx));
    h4.appendChild(bubble); h4.appendChild(textNode(" " + (title || ("Item " + idx))));
    wrap.appendChild(h4);
    if (body) { const p = document.createElement("p"); p.appendChild(textNode(body)); wrap.appendChild(p); }
    if (refs && refs.length) {
      const row = document.createElement("div"); row.className = "sources";
      refs.slice(0, 6).forEach(r => row.appendChild(chip(r)));
      wrap.appendChild(row);
    }
    return wrap;
  }

  function renderAnswer(raw) {
    const text = String(raw || "").replace(/\r/g, "");

    // Split sections by markdown headings (### Solutions)
    const solHeader = /(?:^|\n)\s*(?:#{1,6}\s*|[*_]{2})?\s*solutions?\b[^\n:]*:?[\t ]*(?:\n|$)/i;
    const solMatch = text.match(solHeader);
    let pre  = solMatch ? text.slice(0, solMatch.index) : text;
    let post = solMatch ? text.slice(solMatch.index + solMatch[0].length) : "";

    // Fallback: plain 'Solutions:' anywhere on its own line
    if (!solMatch) {
        const m2 = text.match(/(?:^|\n)\s*solutions?\b[^\n:]*:\s*/i);
        if (m2) {
            pre  = text.slice(0, m2.index);
            post = text.slice(m2.index + m2[0].length);
        }
    }


    const frag = document.createDocumentFragment();

    // Lead (first paragraph before list)
    const leadMatch = pre.match(/^[\s\S]*?(?=\n\s*1\.\s+|$)/);
    if (leadMatch && leadMatch[0].trim()) {
      const lead = document.createElement("div"); lead.className = "answer-lead";
      lead.appendChild(textNode(leadMatch[0].trim().replace(/^#+\s*/,'').trim()));
      frag.appendChild(lead);
    }

    // Numbered challenges
    const listMatches = [...pre.matchAll(/(?:^|\n)\s*(\d+)\.\s+([\s\S]*?)(?=\n\s*\d+\.|\n*$)/g)];
    if (listMatches.length) {
      const block = document.createElement("div"); block.className = "answer-block";
      listMatches.forEach(m => {
        const idx = m[1]; let body = (m[2] || "").trim();
        let title = null, rest = body;
        const bold = body.match(/\*\*(.*?)\*\*\s*:?\s*(.*)/);
        if (bold) { title = bold[1].trim(); rest = bold[2].trim(); }
        else {
          const c = body.indexOf(":"); if (c > 0) { title = body.slice(0, c).trim(); rest = body.slice(c + 1).trim(); }
        }
        const { text: t, refs } = parseSources(rest);
        block.appendChild(cardItem(idx, title, t, refs));
      });
      frag.appendChild(block);
    }

    // Solutions: bullets (“- ”) or anything left as fallback
    if (post.trim()) {
      // allow blank lines and multi-line bullets
      const bullets = [...post.matchAll(/(?:^|\n)[-\u2022*]\s+([\s\S]*?)(?=\n\s*[-\u2022*]|\n*$)/g)].map(m => m[1].trim());
      const numbered = [...post.matchAll(/(?:^|\n)\s*\d+\.\s+([\s\S]*?)(?=\n\s*\d+\.|\n*$)/g)].map(m => m[1].trim());
      const items = numbered.length ? numbered : bullets;

      const sc = document.createElement("div"); sc.className = "solutions-card";
      const h = document.createElement("h4"); h.appendChild(textNode("Solutions")); sc.appendChild(h);

      if (items.length) {
        const ul = document.createElement("ul"); ul.className = "solutions-list";
        items.forEach(it => {
          const { text: t, refs } = parseSources(it);
          const li = document.createElement("li"); li.appendChild(textNode(t));
          if (refs.length) {
            const row = document.createElement("div"); row.className = "sources";
            refs.forEach(r => row.appendChild(chip(r)));
            li.appendChild(row);
          }
          ul.appendChild(li);
        });
        sc.appendChild(ul);
      } else {
        const p = document.createElement("p"); p.appendChild(textNode(post.trim())); sc.appendChild(p);
      }
      frag.appendChild(sc);
    }

    // Fallback: if nothing visible, show as plain text
    if (!frag.textContent.trim()) {
      const p = document.createElement("p"); p.appendChild(textNode(text.trim() || "—"));
      frag.appendChild(p);
    }

    const details = document.createElement('details');
    const sum = document.createElement('summary'); sum.textContent = 'Full answer (raw)';
    pre = document.createElement('pre'); pre.style.whiteSpace = 'pre-wrap'; pre.textContent = text;
    details.appendChild(sum); details.appendChild(pre);
    frag.appendChild(details);

    return frag;
  }

  // ---- Graph summary (same logic as before, kept self-contained) ----
  function _normSig(s){ return String(s||'').toLowerCase().replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim(); }
  function _similar(a,b){
    const A=new Set(_normSig(a).split(' ')), B=new Set(_normSig(b).split(' ')); if(!A.size||!B.size) return false;
    let inter=0; A.forEach(t=>{ if(B.has(t)) inter++; }); const j=inter/Math.max(1, A.size+B.size-inter); return j>0.85;
  }
  function uniqBySimilarity(list){ const out=[]; list.forEach(x=>{ if(x && !out.some(y=>y===x||_similar(x,y))) out.push(x); }); return out; }

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
      if (it.keyword) meta.appendChild(chip(it.keyword,'kbadge'));
      if (it.paper) meta.appendChild(chip(it.paper,'pbadge'));
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
    name: "gpt-4o",
    matches(meta) {
      const p = (meta?.provider || "").toUpperCase();
      const m = (meta?.model || "").toLowerCase();
      return p.includes("OPENAI") && m.includes("gpt-4o");
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
