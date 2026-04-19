from http.server import BaseHTTPRequestHandler
import cgi
import io
import zipfile
import json
import uuid

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
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

        # تحديد اتجاه التحويل بناءً على الامتداد
        is_java_to_bedrock = filename.lower().endswith('.jar')

        with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            try:
                with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_in:
                    for file_info in zip_in.infolist():
                        content = zip_in.read(file_info.filename)
                        
                        if is_java_to_bedrock:
                            # من Java إلى Bedrock: نقل الصور للمسار الجديد
                            if "assets/" in file_info.filename and file_info.filename.endswith(".png"):
                                new_path = "textures/" + file_info.filename.split("textures/")[-1]
                                zip_out.writestr(new_path, content)
                        else:
                            # من Bedrock إلى Java: نقل الصور لمسار Fabric
                            if "textures/" in file_info.filename and file_info.filename.endswith(".png"):
                                new_path = "assets/converted_mod/textures/" + file_info.filename.split("textures/")[-1]
                                zip_out.writestr(new_path, content)
            except:
                pass

            if is_java_to_bedrock:
                # إنشاء ملف Manifest للبيدروك (1.21.32+)
                manifest = {
                    "format_version": 2,
                    "header": {
                        "name": filename.split('.')[0],
                        "description": "Converted to Bedrock 1.21.32+",
                        "uuid": str(uuid.uuid4()),
                        "version": [1, 0, 0],
                        "min_engine_version": [1, 21, 30]
                    },
                    "modules": [{"type": "resources", "uuid": str(uuid.uuid4()), "version": [1, 0, 0]}]
                }
                zip_out.writestr('manifest.json', json.dumps(manifest, indent=4))
            else:
                # إنشاء ملف fabric.mod.json للجافا (1.20.1)
                fabric_json = {
                    "schemaVersion": 1,
                    "id": "converted_mod",
                    "version": "1.0.0",
                    "name": filename.split('.')[0],
                    "description": "Converted from Bedrock to Fabric 1.20.1",
                    "license": "MIT",
                    "environment": "*",
                    "depends": {
                        "fabricloader": ">=0.14.22",
                        "minecraft": "~1.20.1"
                    }
                }
                zip_out.writestr('fabric.mod.json', json.dumps(fabric_json, indent=4))

        # إرسال النتيجة
        converted_data = output_buffer.getvalue()
        new_ext = '.mcaddon' if is_java_to_bedrock else '.jar'
        new_filename = filename.rsplit('.', 1)[0] + new_ext

        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Disposition', f'attachment; filename="{new_filename}"')
        self.end_headers()
        self.wfile.write(converted_data)
