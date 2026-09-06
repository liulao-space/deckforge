/* ============================================================
   DeckForge · transport (pager + rail + cursor). Do not hand-edit.
   Works with any number of <section class="section"> slides.
   ============================================================ */
(function(){
  "use strict";
  var sections = Array.prototype.slice.call(document.querySelectorAll('.section'));
  var deck = document.getElementById('deck');
  var marker = document.getElementById('marker');
  var rail = document.getElementById('rail');
  var side = document.getElementById('side');
  var halo = document.getElementById('halo');
  var cursor = document.getElementById('cursor');
  var n = sections.length, lastIdx = -1, busy = false, sideTimer = null;
  if(n === 0) return; // empty deck: nothing to wire up

  function at(i){ return Math.max(0, Math.min(n-1, i)); }
  function markerRange(){ var h = rail.clientHeight - marker.offsetHeight; return h > 0 ? h : 0; }

  // create rail dots
  var dots = document.getElementById('dots');
  if(dots){ sections.forEach(function(_,k){ var d=document.createElement('div'); d.className='dot'; d.addEventListener('click',function(){ go(k); }); dots.appendChild(d); }); }

  function showSide(idx){
    if(side){ side.textContent = sections[idx].getAttribute('data-title') || ''; side.classList.add('show');
      var mTop = markerRange() * (idx/(n-1));
      if(halo){ halo.style.top = (mTop + marker.offsetHeight/2) + 'px'; halo.classList.remove('on'); void halo.offsetWidth; halo.classList.add('on'); }
      clearTimeout(sideTimer); sideTimer = setTimeout(function(){ side.classList.remove('show'); }, 1600); }
  }

  function go(idx, instant){
    idx = at(idx); if(idx === lastIdx) return;
    busy = true;
    if(lastIdx !== -1) sections[lastIdx].classList.remove('in');
    sections[idx].classList.add('in');
    deck.style.transform = 'translateY(-' + (idx*100) + 'vh)';
    marker.style.top = markerRange() * (idx/(n-1)) + 'px';
    // restart terminal line typing on the slide
    sections[idx].querySelectorAll('.ln').forEach(function(el){ el.style.animation='none'; void el.offsetWidth; el.style.animation=''; });
    showSide(idx); lastIdx = idx;
    setTimeout(function(){ busy = false; }, instant ? 0 : 780);
  }

  function innerScroll(section, deltaY){
    var w = section.querySelector('.wrap'); if(!w) return false;
    if(w.scrollHeight <= w.clientHeight + 1) return false;
    var isDown = deltaY > 0;
    var atEnd = w.scrollTop + w.clientHeight >= w.scrollHeight - 1;
    var atStart = w.scrollTop <= 1;
    if(isDown && !atEnd){ w.scrollTop += deltaY; return true; }
    if(!isDown && !atStart){ w.scrollTop += deltaY; return true; }
    return false;
  }

  // Wheel: inner content first, then page — with an ACCUMULATION threshold so a
  // single trackpad/mouse gesture (many small deltaY) turns into exactly ONE page.
  var wheelAcc = 0, WHEEL_THRESHOLD = 120, wheelTimer = null;
  document.querySelector('.viewport').addEventListener('wheel', function(e){
    e.preventDefault();
    if(busy){ wheelAcc = 0; return; }           // mid-transition: ignore & reset
    var sec = sections[lastIdx];
    if(innerScroll(sec, e.deltaY)) return;      // let inner content scroll
    wheelAcc += e.deltaY;
    // idle decay: a pause resets accumulation so stale deltas never stack up
    clearTimeout(wheelTimer);
    wheelTimer = setTimeout(function(){ wheelAcc = 0; }, 240);
    if(Math.abs(wheelAcc) >= WHEEL_THRESHOLD){   // only flip when enough accumulated
      var dir = wheelAcc > 0 ? 1 : -1;
      wheelAcc = 0; clearTimeout(wheelTimer);
      go(lastIdx + dir);
    }
  }, {passive:false});

  // touch
  var tY = null;
  document.addEventListener('touchstart', function(e){ tY = e.touches[0].clientY; }, {passive:true});
  document.addEventListener('touchmove', function(e){
    if(tY === null || busy) return;
    var dy = tY - e.touches[0].clientY, w = sections[lastIdx].querySelector('.wrap');
    if(w && w.scrollHeight > w.clientHeight + 1){
      var atEnd = w.scrollTop + w.clientHeight >= w.scrollHeight - 1, atStart = w.scrollTop <= 1;
      if((dy > 0 && !atEnd) || (dy < 0 && !atStart)) return;
    }
    e.preventDefault();
  }, {passive:false});
  document.addEventListener('touchend', function(e){
    if(tY === null || busy){ tY = null; return; }
    var dy = tY - e.changedTouches[0].clientY; tY = null;
    var w = sections[lastIdx].querySelector('.wrap');
    if(w && w.scrollHeight > w.clientHeight + 1){
      var atEnd = w.scrollTop + w.clientHeight >= w.scrollHeight - 1, atStart = w.scrollTop <= 1;
      if(Math.abs(dy) > 40){ if((dy > 0 && !atEnd) || (dy < 0 && !atStart)){ w.scrollTop += dy*2; return; } }
    }
    if(Math.abs(dy) > 40) go(lastIdx + (dy > 0 ? 1 : -1));
  }, {passive:true});

  document.addEventListener('keydown', function(e){
    if(['ArrowDown','ArrowRight','PageDown',' '].includes(e.key)){ e.preventDefault(); go(lastIdx+1); }
    else if(['ArrowUp','ArrowLeft','PageUp'].includes(e.key)){ e.preventDefault(); go(lastIdx-1); }
  });

  window.addEventListener('resize', function(){
    deck.style.transform = 'translateY(-' + (lastIdx*100) + 'vh)';
    marker.style.top = markerRange() * (lastIdx/(n-1)) + 'px';
  });

  // custom cursor
  if(matchMedia('(pointer:fine)').matches && cursor){
    var cx = innerWidth/2, cy = innerHeight/2, mx = cx, my = cy;
    document.addEventListener('mousemove', function(e){ mx = e.clientX; my = e.clientY; });
    document.addEventListener('mousedown', function(){ cursor.classList.add('press'); });
    document.addEventListener('mouseup', function(){ cursor.classList.remove('press'); });
    (function loop(){ cx += (mx-cx)*.45; cy += (my-cy)*.45; cursor.style.transform = 'translate('+cx+'px,'+cy+'px)'; requestAnimationFrame(loop); })();
  }

  lastIdx = 0; sections[0].classList.add('in'); deck.style.transform = 'translateY(0)'; marker.style.top = '0px'; showSide(0);
})();
