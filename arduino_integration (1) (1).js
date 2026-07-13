// ─────────────────────────────────────────────────────────
// ADD THIS to your doorx.html inside the <script> tag
// Replace your existing triggerDoor() function with this one
// ─────────────────────────────────────────────────────────

const BACKEND = 'http://localhost:5000';

// Check if Python server is running
async function checkBackend() {
  try {
    const res = await fetch(BACKEND + '/status');
    const data = await res.json();
    console.log('Backend:', data);
    document.getElementById('f-inf').textContent = data.arduino === 'connected' ? 'ARDUINO OK' : 'SIM MODE';
  } catch(e) {
    console.log('Backend not running — Arduino commands disabled');
  }
}
checkBackend();

// Replace your existing triggerDoor() with this version
function triggerDoor(state, personName, confidence) {
  if(doorTimer) clearTimeout(doorTimer);
  const bar = document.getElementById('door-bar');
  const txt = document.getElementById('door-txt');

  if(state === 'open') {
    bar.className = 'door-bar door-open';
    txt.textContent = 'ACCESS GRANTED — DOOR OPEN';
    stats.auth++; stats.total++;
    document.getElementById('s-auth').textContent = stats.auth;

    // ── SEND TO ARDUINO via Python ──
    fetch(BACKEND + '/access', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        name: personName || 'Authorized',
        decision: 'grant',
        confidence: confidence || 0
      })
    }).then(r => r.json())
      .then(d => console.log('Arduino response:', d))
      .catch(e => console.log('Backend offline, Arduino skipped'));

  } else {
    bar.className = 'door-bar door-denied';
    txt.textContent = 'ACCESS DENIED — ALARM TRIGGERED';
    stats.deny++; stats.total++;
    document.getElementById('s-deny').textContent = stats.deny;

    // ── SEND TO ARDUINO via Python ──
    fetch(BACKEND + '/access', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        name: personName || 'Unknown',
        decision: 'deny',
        confidence: confidence || 0
      })
    }).then(r => r.json())
      .then(d => console.log('Arduino response:', d))
      .catch(e => console.log('Backend offline, Arduino skipped'));
  }

  document.getElementById('s-total').textContent = stats.total;

  doorTimer = setTimeout(() => {
    bar.className = 'door-bar door-closed';
    txt.textContent = 'STANDBY — AWAITING SCAN';
    lastResult = null;
  }, 4000);
}
