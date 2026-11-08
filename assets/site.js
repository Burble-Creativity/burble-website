/* Shared across every page: store links, theme toggle, nav, mobile menu, scroll reveal */
/* ============ App store links ============
   Every App Store / Google Play button on the page uses these. */
const STORE_LINKS = {
  ios: "https://apps.apple.com/us/app/burble-neuro/id6775283680",
  android: "https://play.google.com/store/apps/details?id=com.burbleneuro.app"
};

document.querySelectorAll('[data-store]').forEach(a=>{
  const url=STORE_LINKS[a.dataset.store];
  if(url){a.href=url;a.target="_blank";a.rel="noopener"}
});

/* ============ Theme toggle (remembered per visitor) ============ */
const root=document.documentElement;
const metaTheme=document.querySelector('meta[name="theme-color"]');
function applyTheme(t){
  root.setAttribute('data-theme',t);
  metaTheme.setAttribute('content',t==='light'?'#f6f7f9':'#05060a');
  const next=t==='light'?'dark':'light';
  document.querySelectorAll('[data-theme-toggle]').forEach(b=>b.setAttribute('aria-label','Switch to '+next+' mode'));
  document.querySelectorAll('[data-theme-label]').forEach(s=>s.textContent=t==='light'?'Light mode':'Dark mode');
}
applyTheme(root.getAttribute('data-theme')||'dark');
document.querySelectorAll('[data-theme-toggle]').forEach(b=>b.addEventListener('click',()=>{
  const t=root.getAttribute('data-theme')==='light'?'dark':'light';
  applyTheme(t);
  try{localStorage.setItem('burble-theme',t)}catch(e){}
}));

/* nav state */
const nav=document.getElementById('nav');
const onScroll=()=>nav.classList.toggle('scrolled',scrollY>10);
addEventListener('scroll',onScroll,{passive:true});onScroll();

/* mobile drawer */
const btn=document.getElementById('menuBtn'),drawer=document.getElementById('drawer');
btn.addEventListener('click',()=>{const o=drawer.classList.toggle('open');btn.setAttribute('aria-expanded',o);document.body.style.overflow=o?'hidden':''});
drawer.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{drawer.classList.remove('open');btn.setAttribute('aria-expanded',false);document.body.style.overflow=''}));

/* reveal on scroll */
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{rootMargin:'0px 0px -8% 0px'});
document.querySelectorAll('.reveal').forEach((el,i)=>{el.style.transitionDelay=(el.closest('.hero')?i*80:0)+'ms';io.observe(el)});

