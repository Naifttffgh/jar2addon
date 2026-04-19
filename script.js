const zone = document.getElementById('drop-zone');
const input = document.getElementById('file-input');
const idle = document.getElementById('status-idle');
const loading = document.getElementById('status-loading');
const aiInput = document.getElementById('ai-input');

// فتح نافذة اختيار الملفات
zone.onclick = () => input.click();

// التعامل مع سحب الملفات
zone.ondragover = (e) => { e.preventDefault(); zone.classList.add('active'); };
zone.ondragleave = () => zone.classList.remove('active');
zone.ondrop = (e) => {
    e.preventDefault();
    zone.classList.remove('active');
    handleProcess(e.dataTransfer.files[0]);
};

input.onchange = (e) => handleProcess(e.target.files[0]);

// وظيفة البناء بناءً على النص (AI Build)
function buildWithAI() {
    const text = aiInput.value.trim();
    if (!text) {
        alert("اكتب أمراً أولاً!");
        return;
    }
    const blob = new Blob([text], { type: 'text/plain' });
    const file = new File([blob], "ai_request.txt");
    handleProcess(file);
}

function handleProcess(file) {
    if (!file) return;

    // إظهار حالة التحميل
    idle.classList.add('hidden');
    loading.classList.remove('hidden');

    const fd = new FormData();
    fd.append('file', file);

    fetch('/api/convert', { method: 'POST', body: fd })
    .then(res => {
        if (!res.ok) throw new Error("Server Error");
        return res.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // النتيجة دائماً ملف JAR كما طلبت
        a.download = file.name.split('.')[0] + ".jar";
        a.click();
        resetUI();
    })
    .catch(err => {
        alert('حدث خطأ في عملية البناء!');
        console.error(err);
        resetUI();
    });
}

function resetUI() {
    idle.classList.remove('hidden');
    loading.classList.add('hidden');
}
