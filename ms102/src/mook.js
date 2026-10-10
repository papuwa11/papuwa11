(function(){
  // 腕試し：選んだ瞬間に採点して解説を出す
  var right = 0;
  var scoreEl = document.getElementById('score');
  Array.prototype.forEach.call(document.querySelectorAll('.qz'), function(q){
    var ans = q.getAttribute('data-answer');
    var why = q.querySelector('.why');
    Array.prototype.forEach.call(q.querySelectorAll('.opt'), function(b){
      b.addEventListener('click', function(){
        if (q.classList.contains('done')) return;
        q.classList.add('done');
        Array.prototype.forEach.call(q.querySelectorAll('.opt'), function(o){
          if (o.getAttribute('data-k') === ans) o.classList.add('right');
          o.setAttribute('aria-disabled', 'true');
        });
        if (b.getAttribute('data-k') === ans) { right++; if (scoreEl) scoreEl.textContent = String(right); }
        else { b.classList.add('wrong'); }
        if (why) why.hidden = false;
      });
    });
  });

  // 上部バー：いま読んでいるカードの番号を光らせる
  var chips = {};
  Array.prototype.forEach.call(document.querySelectorAll('.tb-chips a'), function(a){
    chips[a.getAttribute('href').slice(1)] = a;
  });
  var current = null;
  function mark(id){
    if (id === current) return;
    if (current && chips[current]) chips[current].classList.remove('here');
    current = id;
    if (id && chips[id]) {
      chips[id].classList.add('here');
      var bar = chips[id].parentNode, r = chips[id].getBoundingClientRect(), b = bar.getBoundingClientRect();
      if (r.left < b.left || r.right > b.right) bar.scrollLeft += (r.left - b.left) - b.width / 2 + r.width / 2;
    }
  }
  var targets = Array.prototype.slice.call(document.querySelectorAll('.card, #quiz, #memo'));
  function onScroll(){
    var best = null;
    for (var i = 0; i < targets.length; i++) {
      if (targets[i].getBoundingClientRect().top <= 120) best = targets[i].id; else break;
    }
    mark(best);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
