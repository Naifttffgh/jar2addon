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

            # تحديد الاتجاه
            is_java_to_bedrock = filename.lower().endswith('.jar')

            with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                try:
                    with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zip_in:
                        for file_info in zip_in.infolist():
                            content = zip_in.read(file_info.filename)
                            
                            if is_java_to_bedrock:
                                # من جافا إلى بيدروك (نقل الأنسجة)
                                if "textures/" in file_info.filename and file_info.filename.endswith(".png"):
                                    clean_name = file_info.filename.split("/")[-1]
                                    zip_out.writestr(f"textures/{clean_name}", content)
                            else:
                                # من بيدروك إلى جافا (ترتيب مجلدات Fabric 1.20.1)
                                if "textures/" in file_info.filename and file_info.filename.endswith(".png"):
                                    clean_name = file_info.filename.split("/")[-1]
                                    # مسار الفابريك القياسي للأصول
                                    zip_out.writestr(f"assets/mc_transformer/textures/item/{clean_name}", content)
                except:
                    pass

                if is_java_to_bedrock:
                    # إعدادات البيدروك 1.21.32+
                    manifest = {
                        "format_version": 2,
                        "header": {
                            "name": filename.rsplit('.', 1)[0],
                            "description": "Converted to Bedrock 1.21.32+",
                            "uuid": str(uuid.uuid4()),
                            "version": [1, 0, 0],
                            "min_engine_version": [1, 21, 30] # متوافق مع 1.21.32
                        },
                        "modules": [{"type": "resources", "uuid": str(uuid.uuid4()), "version": [1, 0, 0]}]
                    }
                    zip_out.writestr('manifest.json', json.dumps(manifest, indent=4))
                else:
                    # إعدادات Fabric 1.20.1
                    fabric_json = {
                        "schemaVersion": 1,
                        "id": "mc_transformer",
                        "version": "1.0.0",
                        "name": filename.rsplit('.', 1)[0],
                        "description": "Converted to Fabric 1.20.1",
                        "depends": {
                            "fabricloader": ">=0.14.22",
                            "minecraft": "1.20.1"
                        }
                    }
                    zip_out.writestr('fabric.mod.json', json.dumps(fabric_json, indent=4))

            # تجهيز البيانات للتحميل
            converted_data = output_buffer.getvalue()
            new_ext = '.mcaddon' if is_java_to_bedrock else '.jar'
            new_filename = filename.rsplit('.', 1)[0] + new_ext

            self.send_response(200)
            # أهم سطرين لمنع ظهور "الزفت" (النصوص الغريبة)
            self.send_header('Content-Type', 'application/zip') 
            self.send_header('Content-Disposition', f'attachment; filename="{new_filename}"')
            self.send_header('Content-Length', str(len(converted_data)))
            self.end_headers()
            
            self.wfile.write(converted_data)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
