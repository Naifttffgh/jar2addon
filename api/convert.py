from http.server import BaseHTTPRequestHandler
import cgi
import io

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # التعامل مع البيانات المرفوعة عبر الـ Form
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        if "file" not in form:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No file uploaded")
            return

        file_item = form["file"]
        file_content = file_item.file.read()
        filename = file_item.filename

        # --- منطقة التحويل الذكي ---
        # هنا سنضع خوارزمية فك الـ JAR وإعادة بنائه كـ MCADDON
        # حالياً سيعيد الملف كما هو للتأكد من نجاح العملية
        # --------------------------

        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Disposition', f'attachment; filename="converted_{filename}"')
        self.end_headers()
        
        # إرسال الملف المحول للمستخدم
        self.wfile.write(file_content)
        return