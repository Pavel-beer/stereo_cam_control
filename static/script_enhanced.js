// Элементы DOM
const videoImg = document.getElementById('video');
const fpsSpan = document.getElementById('fps');
const panSlider = document.getElementById('pan');
const tiltSlider = document.getElementById('tilt');
const panVal = document.getElementById('panVal');
const tiltVal = document.getElementById('tiltVal');
const viewModeSelect = document.getElementById('viewMode');
const resolutionSelect = document.getElementById('resolution');
const snapshotBtn = document.getElementById('snapshotBtn');
const homeBtn = document.getElementById('homeBtn');
const fpsStatusSpan = document.getElementById('fpsStatus');

// Функция обновления статуса (FPS и пр.)
async function updateStatus() {
    try {
        const res = await fetch('/status');
        const data = await res.json();
        fpsSpan.textContent = data.fps;
        fpsStatusSpan.textContent = data.fps;
        if (panSlider.value != data.pan) panSlider.value = data.pan;
        if (tiltSlider.value != data.tilt) tiltSlider.value = data.tilt;
        panVal.textContent = data.pan;
        tiltVal.textContent = data.tilt;
    } catch(e) {
        console.error('Status error', e);
    }
}

// Отправка команды сервоприводу
async function sendCommand(endpoint, value = '') {
    try {
        let url = endpoint;
        if (value !== '') url += '/' + value;
        await fetch(url);
    } catch(e) { console.error(e); }
}

// События слайдеров
panSlider.oninput = () => {
    let val = panSlider.value;
    panVal.textContent = val;
    sendCommand('/move_pan', val);
};
tiltSlider.oninput = () => {
    let val = tiltSlider.value;
    tiltVal.textContent = val;
    sendCommand('/move_tilt', val);
};

// Кнопка "Домой"
homeBtn.onclick = async () => {
    await fetch('/move_home');
    const res = await fetch('/status');
    const data = await res.json();
    panSlider.value = data.pan;
    tiltSlider.value = data.tilt;
    panVal.textContent = data.pan;
    tiltVal.textContent = data.tilt;
};

// Смена режима отображения
viewModeSelect.onchange = async () => {
    const mode = viewModeSelect.value;
    await fetch(`/set_view_mode?mode=${mode}`);
};

// Смена разрешения
resolutionSelect.onchange = async () => {
    const [width, height] = resolutionSelect.value.split('x');
    await fetch(`/set_resolution?width=${width}&height=${height}`);
};

// Снимок
snapshotBtn.onclick = () => {
    window.open('/snapshot', '_blank');
};

// Обновление статуса каждую секунду
setInterval(updateStatus, 1000);
updateStatus();
