/* dc-mini.js — runtime mínimo (≈150 líneas) de plantillas para las páginas del sitio. Cubre solo lo que usan Main y Historia:
 *   · «{{a.b.c}}» en texto y atributos (búsqueda con puntos; no hay expresiones)
 *   · <sc-for list="{{lista}}" as="x">, <sc-if value="{{v}}">
 *   · onClick / onChange con funciones, ref="{{fn}}" (se llama una vez por elemento nuevo)
 *   · data-style="{{estilo}}" se dibuja como style (así el editor no valida la marca como CSS)
 *   · renderVals().cssVars = { tinta: '#…' } define --tinta en la raíz, para usar var(--tinta) en los style
 *   · class Component extends DCLogic { constructor, componentDidMount, renderVals, setState, forceUpdate }
 * Redibuja con morphdom (se carga antes) para no destruir el mapa, los sliders ni el foco.
 * Licencia: MIT (este archivo). morphdom: MIT, https://github.com/patrick-steele-idem/morphdom
 */
(function () {
  'use strict';
  const VOID = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr']);
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const escA = (s) => esc(s).replace(/"/g, '&quot;');
  const HOLE = /\{\{\s*([^}]*?)\s*\}\}/g, WHOLE = /^\{\{\s*([^}]*?)\s*\}\}$/;

  class DCLogic {
    constructor(props) { this.props = props || {}; this.state = this.state || {}; }
    setState(o) { this.state = Object.assign({}, this.state, typeof o === 'function' ? o(this.state) : o); this.forceUpdate(); }
    forceUpdate() { if (this.__dc) this.__dc.schedule(); }
  }

  function lookup(scope, path) {
    if (/^(true|false)$/.test(path)) return path === 'true';
    const parts = path.split('.');
    let v;
    for (let i = scope.length - 1; i >= 0; i--) { if (parts[0] in scope[i]) { v = scope[i][parts[0]]; break; } }
    for (let k = 1; k < parts.length && v != null; k++) v = v[parts[k]];
    return v;
  }

  class Runtime {
    constructor(Comp, props, tpl, root) {
      this.inst = new Comp(props); this.inst.__dc = this; this.tpl = tpl; this.root = root;
      this.handlers = []; this.refs = []; this.seen = new WeakSet(); this.pending = false; this.mounted = false;
      const on = (ev, attr) => root.addEventListener(ev, (e) => {
        const el = e.target.closest && e.target.closest('[' + attr + ']'); if (!el || !root.contains(el)) return;
        const h = this.handlers[+el.getAttribute(attr)]; if (h) h(e);
      });
      on('click', 'data-dc-click');
      on('input', 'data-dc-input'); on('change', 'data-dc-change');
      this.render();
      this.mounted = true;
      if (this.inst.componentDidMount) this.inst.componentDidMount();
    }
    schedule() { if (this.pending) return; this.pending = true; requestAnimationFrame(() => { this.pending = false; this.render(); }); }
    render() {
      const vals = this.inst.renderVals ? this.inst.renderVals() : {};
      if (vals.cssVars) Object.keys(vals.cssVars).forEach((k) => this.root.style.setProperty('--' + k, vals.cssVars[k]));
      this.handlers = []; this.refs = [];
      const html = this.node(this.tpl.content, [vals]);
      const next = document.createElement('div'); next.id = this.root.id; next.className = this.root.className; next.innerHTML = html;
      morphdom(this.root, next, {
        childrenOnly: true,
        onBeforeElUpdated: (from, to) => !(from.hasAttribute('data-dc-ref') && to.hasAttribute('data-dc-ref') && this.seen.has(from))
      });
      this.root.querySelectorAll('[data-dc-value]').forEach((el) => { const v = el.getAttribute('data-dc-value'); if (el.value !== v) el.value = v; });
      this.root.querySelectorAll('[data-dc-ref]').forEach((el) => { if (this.seen.has(el)) return; this.seen.add(el); const f = this.refs[+el.getAttribute('data-dc-ref')]; if (typeof f === 'function') f(el); });
    }
    node(n, scope) {
      if (n.nodeType === 3) return esc(n.nodeValue).replace(HOLE, (_, p) => { const v = lookup(scope, p); return v == null || v === false ? '' : esc(v); });
      if (n.nodeType !== 1 && n.nodeType !== 11) return '';
      const src = n.tagName === 'TEMPLATE' ? n.content : n;
      const kids = (sc) => Array.prototype.map.call(src.childNodes, (c) => this.node(c, sc)).join('');
      if (n.nodeType === 11) return kids(scope);
      const tag = n.tagName.toLowerCase(), sct = n.getAttribute && n.getAttribute('data-sc');
      if (sct === 'for') {
        const list = lookup(scope, n.getAttribute('list').match(WHOLE)[1]) || [], as = n.getAttribute('as');
        return list.map((it, i) => kids(scope.concat([{ [as]: it, index: i }]))).join('');
      }
      if (sct === 'if') {
        const m = n.getAttribute('value').match(WHOLE);
        return m && lookup(scope, m[1]) ? kids(scope) : '';
      }
      let attrs = '';
      Array.prototype.forEach.call(n.attributes, (a) => {
        const name = a.name;
        if (name.startsWith('hint-placeholder') || name === 'data-sc') return;
        const whole = a.value.match(WHOLE);
        if (/^on(click|change|input)$/i.test(name) && whole) {
          const f = lookup(scope, whole[1]); if (typeof f !== 'function') return;
          const ev = name.slice(2).toLowerCase(); let kind = ev;
          if (ev === 'change' && n.tagName === 'INPUT' && n.getAttribute('type') === 'range') kind = 'input';
          attrs += ' data-dc-' + kind + '="' + this.handlers.length + '"'; this.handlers.push(f); return;
        }
        if (name === 'ref' && whole) { attrs += ' data-dc-ref="' + this.refs.length + '"'; this.refs.push(lookup(scope, whole[1])); return; }
        if (whole) {
          const v = lookup(scope, whole[1]);
          if (name === 'data-style') { if (v != null && v !== false) attrs += ' style="' + escA(v) + '"'; return; }
          if (name === 'value') { attrs += ' data-dc-value="' + escA(v == null ? '' : v) + '" value="' + escA(v == null ? '' : v) + '"'; return; }
          if (typeof v === 'boolean') { if (/^(aria|data)-/.test(name)) attrs += ' ' + name + '="' + v + '"'; else if (v) attrs += ' ' + name + '=""'; return; }
          if (v == null) return;
          attrs += ' ' + name + '="' + escA(v) + '"'; return;
        }
        attrs += ' ' + name + '="' + escA(a.value.replace(HOLE, (_, p) => { const v = lookup(scope, p); return v == null || v === false ? '' : v; })) + '"';
      });
      if (VOID.has(tag)) return '<' + tag + attrs + '>';
      return '<' + tag + attrs + '>' + kids(scope) + '</' + tag + '>';
    }
  }

  window.DCLogic = DCLogic;
  window.DC = {
    mount(Comp, propsSpec, tplId, rootId) {
      const props = {}; Object.keys(propsSpec || {}).forEach((k) => { if (k[0] !== '$' && propsSpec[k] && 'default' in propsSpec[k]) props[k] = propsSpec[k].default; });
      return new Runtime(Comp, props, document.getElementById(tplId), document.getElementById(rootId));
    }
  };
})();
