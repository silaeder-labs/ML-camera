let selectedId = null;
let mode = 'normal';
let trackingMode = 'face';

function updateModeUI() {
    let overlay = document.getElementById('overlay');
    let normalBtn = document.getElementById('mode-normal');
    let sniperBtn = document.getElementById('mode-sniper');

    if (!overlay || !normalBtn || !sniperBtn) {
        return;
    }

    overlay.classList.remove('normal', 'sniper');
    overlay.classList.add(mode);

    normalBtn.classList.toggle('selected', mode === 'normal');
    sniperBtn.classList.toggle('selected', mode === 'sniper');
}

function bindModeButtons() {
    let normalBtn = document.getElementById('mode-normal');
    let sniperBtn = document.getElementById('mode-sniper');

    if (!normalBtn || !sniperBtn) {
        return;
    }

    normalBtn.onclick = () => {
        mode = 'normal';
        updateModeUI();
    };

    sniperBtn.onclick = () => {
        mode = 'sniper';
        updateModeUI();
    };
}

async function updateTrackingMode(modeName) {
    try {
        let response = await fetch('/tracking_mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                mode: modeName
            })
        });

        let data = await response.json();

        if (data.mode) {
            trackingMode = data.mode;
            let video = document.getElementById('video-stream');
            if (video) {
                video.src = '/video_feed?t=' + Date.now();
            }
        }
    } catch (err) {
        console.log(err);
    }
}

function updateTrackingButtons() {
    let faceBtn = document.getElementById('tracking-face');
    let bodyBtn = document.getElementById('tracking-body');

    if (!faceBtn || !bodyBtn) {
        return;
    }

    faceBtn.classList.toggle('selected', trackingMode === 'face');
    bodyBtn.classList.toggle('selected', trackingMode === 'body');
}

function bindTrackingButtons() {
    let faceBtn = document.getElementById('tracking-face');
    let bodyBtn = document.getElementById('tracking-body');

    if (!faceBtn || !bodyBtn) {
        return;
    }

    faceBtn.onclick = async () => {
        await updateTrackingMode('face');
        updateTrackingButtons();
    };

    bodyBtn.onclick = async () => {
        await updateTrackingMode('body');
        updateTrackingButtons();
    };
}

async function loadTrackingMode() {
    try {
        let response = await fetch('/tracking_mode');
        let data = await response.json();

        if (data.mode) {
            trackingMode = data.mode;
        }
    } catch (err) {
        console.log(err);
    }
}

async function updateButtons() {
    let response = await fetch('/tracking_state');
    let data = await response.json();
    let ids = data.ids || [];
    let colors = data.colors || {};

    let container = document.getElementById('buttons');
    let info = document.getElementById('info');

    container.innerHTML = '';

    if (ids.length === 0) {
        container.innerText = 'Нет активных ID';
        selectedId = null;
        info.innerHTML = 'Выберите ID';
        return;
    }

    if (selectedId === null || !ids.includes(selectedId)) {
        selectedId = ids[0];
        info.innerHTML = 'Выбран ID: ' + selectedId;
    }

    ids.forEach(id => {
        let btn = document.createElement('button');
        btn.innerText = 'ID ' + id;

        let colorKey = String(id);
        let color = colors[colorKey];

        if (color) {
            btn.style.backgroundColor = color;
            btn.style.borderColor = color;

            let r = parseInt(color.slice(1, 3), 16);
            let g = parseInt(color.slice(3, 5), 16);
            let b = parseInt(color.slice(5, 7), 16);
            let luminance = (0.299 * r + 0.587 * g + 0.114 * b);
            btn.style.color = luminance > 140 ? '#111' : '#fff';
        } else {
            btn.style.backgroundColor = '';
            btn.style.borderColor = '';
            btn.style.color = '';
        }

        if (id === selectedId) {
            btn.classList.add('selected');
        }

        btn.onclick = () => {
            selectedId = id;
            info.innerHTML = 'Выбран ID: ' + id;
            updateButtons();
        };

        container.appendChild(btn);
    });
}

async function updateOffset() {
    if (selectedId === null) {
        return;
    }

    try {
        let response = await fetch('/offset/' + selectedId);
        let data = await response.json();

        if (data.error) {
            return;
        }

        document.getElementById('info').innerHTML =
            '<b>ID:</b> ' + data.id +
            '<br><br>' +
            '<b>Центр лица:</b> (' +
            data.face_x + ', ' +
            data.face_y + ')' +
            '<br>' +
            '<b>Центр экрана:</b> (' +
            data.screen_x + ', ' +
            data.screen_y + ')' +
            '<br><br>' +
            '<b>dx:</b> ' + data.dx +
            '<br>' +
            '<b>dy:</b> ' + data.dy +
            '<br><br>' +
            '<b>angels_x:</b> ' + data.angles_x;
    } catch (err) {
        console.log(err);
    }
}

setInterval(updateButtons, 1000);
setInterval(updateOffset, 100);

updateButtons();
bindModeButtons();
updateModeUI();
bindTrackingButtons();
loadTrackingMode().then(updateTrackingButtons);
