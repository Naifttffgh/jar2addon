from http.server import BaseHTTPRequestHandler
import cgi
import io
import zipfile
import json
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
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

            is_java_to_bedrock = filename.lower().endswith('.jar')

            with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                try:
                    with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_in:
                        all_files = zip_in.namelist()
                        
                        for fname in all_files:
                            # --- نظام الذكاء في التنظيف (Smart Cleaning) ---
                            if is_java_to_bedrock:
                                # حذف مخلفات الجافا التي تسبب أخطاء في البيدروك
                                if any(x in fname for x in ['fabric.mod.json', 'META-INF', 'quilt.mod.json', '.class']):
                                    continue
                            else:
                                # حذف ملفات البيدروك عند التحويل للجافا
                                if any(x in fname for x in ['manifest.json', 'pack_icon.png', 'contents.json']):
                                    continue

                            content = zip_in.read(fname)
                            
                            # --- ذكاء تحويل المسارات (Path Intelligence) ---
                            if is_java_to_bedrock:
                                # البحث عن الصور في أي مكان ونقلها لمجلد الأنسجة القياسي
                                if fname.endswith(".png") and "textures" in fname:
                                    clean_name = fname.split("/")[-1]
                                    zip_out.writestr(f"textures/items/{clean_name}", content)
                            else:
                                # تحويل أنسجة البيدروك لمسار Fabric 1.20.1
                                if fname.endswith(".png") and "textures" in fname:
                                    clean_name = fname.split("/")[-1]
                                    zip_out.writestr(f"assets/transformed_mod/textures/item/{clean_name}", content)
                except:
                    pass

                # --- توليد ملفات التعريف الذكية ---
                if is_java_to_bedrock:
                    # بناء مانيفست ذكي يدعم 1.21.32+
                    manifest = {
                        "format_version": 2,
                        "header": {
                            "name": f"{filename.rsplit('.', 1)[0]} (AI Converted)",
                            "description": "Smart conversion for Bedrock 1.21.32+",
                            "uuid": str(uuid.uuid4()),
                            "version": [1, 0, 0],
                            "min_engine_version": [1, 21, 30]
                        },
                        "modules": [{"type": "resources", "uuid": str(uuid.uuid4()), "version": [1, 0, 0]}]
                    }
                    zip_out.writestr('manifest.json', json.dumps(manifest, indent=4))
                else:
                    # بناء ملف Fabric 1.20.1 متوافق
                    fabric_json = {
                        "schemaVersion": 1,
                        "id": "transformed_mod_ai",
                        "version": "1.0.0",
                        "name": filename.rsplit('.', 1)[0],
                        "description": "AI Optimized for Fabric 1.20.1",
                        "depends": {"fabricloader": ">=0.14.22", "minecraft": "1.20.1"}
                    }
                    zip_out.writestr('fabric.mod.json', json.dumps(fabric_json, indent=4))

            # إرسال الملف النهائي
            converted_data = output_buffer.getvalue()
            new_filename = filename.rsplit('.', 1)[0] + ('.mcaddon' if is_java_to_bedrock else '.jar')

            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', f'attachment; filename="{new_filename}"')
            self.end_headers()
            self.wfile.write(converted_data)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal Error: {str(e)}".encode())
