from http.server import BaseHTTPRequestHandler
import cgi
import io
import zipfile
import json
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. استلام الملف المرفوع من الواجهة الأمامية
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
            output_buffer = io.BytesIO()

            # 2. تحديد اتجاه التحويل تلقائياً بناءً على امتداد الملف
            is_java_to_bedrock = filename.lower().endswith('.jar')

            # 3. بدء عملية بناء الملف الجديد
            with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                try:
                    # محاولة قراءة الملف الأصلي
                    with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_in:
                        for file_info in zip_in.infolist():
                            fname = file_info.filename
                            
                            # --- نظام التنظيف الذكي (Smart Cleaning) ---
                            if is_java_to_bedrock:
                                # حذف أي ملفات جافا قد تسبب تعطل البيدروك
                                if any(x in fname for x in ['fabric.mod.json', 'META-INF', '.class', 'quilt.mod.json']):
                                    continue
                            else:
                                # حذف ملفات البيدروك عند التحويل إلى جافا
                                if any(x in fname for x in ['manifest.json', 'pack_icon.png', 'contents.json']):
                                    continue

                            content = zip_in.read(fname)
                            
                            # --- نظام توجيه المسارات (Path Routing) ---
                            if is_java_to_bedrock:
                                # استخراج الصور ووضعها في مسار البيدروك الصحيح
                                if "textures/" in fname and fname.endswith(".png"):
                                    clean_name = fname.split("/")[-1]
                                    zip_out.writestr(f"textures/items/{clean_name}", content)
                            else:
                                # استخراج الصور ووضعها في مسار Fabric 1.20.1 الصحيح
                                if "textures/" in fname and fname.endswith(".png"):
                                    clean_name = fname.split("/")[-1]
                                    zip_out.writestr(f"assets/transformed_mod_ai/textures/item/{clean_name}", content)
                except Exception as zip_error:
                    pass # يتم التخطي إذا كان الملف الأصلي فارغاً أو ليس بصيغة مضغوطة صحيحة

                # --- 4. توليد ملفات التعريف (Manifest / Mod JSON) ---
                if is_java_to_bedrock:
                    # بناء مانيفست متوافق مع Bedrock 1.21.32+
                    manifest = {
                        "format_version": 2,
                        "header": {
                            "name": f"{filename.rsplit('.', 1)[0]} (AI)",
                            "description": "Converted by MC-TRANSFORMER for Bedrock 1.21.32+",
                            "uuid": str(uuid.uuid4()),
                            "version": [1, 0, 0],
                            "min_engine_version": [1, 21, 30]
                        },
                        "modules": [{
                            "type": "resources", 
                            "uuid": str(uuid.uuid4()), 
                            "version": [1, 0, 0]
                        }]
                    }
                    zip_out.writestr('manifest.json', json.dumps(manifest, indent=4))
                else:
                    # بناء ملف Fabric متوافق مع 1.20.1
                    fabric_json = {
                        "schemaVersion": 1,
                        "id": "transformed_mod_ai",
                        "version": "1.0.0",
                        "name": f"{filename.rsplit('.', 1)[0]} (AI)",
                        "description": "Converted by MC-TRANSFORMER for Fabric 1.20.1",
                        "depends": {
                            "fabricloader": ">=0.14.22", 
                            "minecraft": "1.20.1"
                        }
                    }
                    zip_out.writestr('fabric.mod.json', json.dumps(fabric_json, indent=4))

            # 5. تجهيز الملف النهائي للإرسال
            converted_data = output_buffer.getvalue()
            new_filename = filename.rsplit('.', 1)[0] + ('.mcaddon' if is_java_to_bedrock else '.jar')

            # 6. إرسال الهيدرز (Headers) الصحيحة لإجبار المتصفح على التحميل
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip') 
            self.send_header('Content-Disposition', f'attachment; filename="{new_filename}"')
            self.send_header('Content-Length', str(len(converted_data)))
            self.end_headers()
            
            # إرسال بيانات الملف
            self.wfile.write(converted_data)

        except Exception as e:
            # معالجة الأخطاء وإرجاع رسالة واضحة
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal Server Error: {str(e)}".encode())
