const zone = document.getElementById('drop-zone');
const input = document.getElementById('file-input');
const idle = document.getElementById('status-idle');
const loading = document.getElementById('status-loading');

// فتح النافذة عند الضغط
zone.onclick = () => input.click();

// تأثيرات السحب
zone.ondragover = (e) => { e.preventDefault(); zone.classList.add('active'); };
zone.ondragleave = () => zone.classList.remove('active');

zone.ondrop = (e) => {
    e.preventDefault();
    zone.classList.remove('active');
    handleFile(e.dataTransfer.files[0]);
};

input.onchange = (e) => handleFile(e.target.files[0]);

function handleFile(file) {
    if (!file) return;
    
    const name = file.name.toLowerCase();
    if (!name.endsWith('.jar') && !name.endsWith('.mcaddon')) {
        alert('الملف غير مدعوم! استخدم .jar أو .mcaddon');
        return;
    }

    // إظهار اللودر
    idle.classList.add('hidden');
    loading.classList.remove('hidden');

    const fd = new FormData();
    fd.append('file', file);

    // إرسال الملف إلى Vercel Function
    fetch('/api/convert', { method: 'POST', body: fd })
    .then(res => res.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // تغيير الامتداد في اسم الملف المحمل
        a.download = name.endsWith('.jar') ? file.name.replace('.jar', '.mcaddon') : file.name.replace('.mcaddon', '.jar');
        a.click();
        resetUI();
    })
    .catch(() => {
        alert('حدث خطأ أثناء الاتصال بالخادم!');
        resetUI();
    });
}

function resetUI() {
    idle.classList.remove('hidden');
    loading.classList.add('hidden');
}