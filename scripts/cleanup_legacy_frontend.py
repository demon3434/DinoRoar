import os
import shutil

def cleanup_legacy_frontend():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_app = os.path.join(project_root, "backend", "app")
    
    # 1. Delete backend/app/templates
    templates_dir = os.path.join(backend_app, "templates")
    if os.path.exists(templates_dir):
        shutil.rmtree(templates_dir)
        print(f"Deleted directory: {templates_dir}")
    else:
        print("templates directory already gone.")

    # 2. Delete backend/app/static/js
    static_js_dir = os.path.join(backend_app, "static", "js")
    if os.path.exists(static_js_dir):
        shutil.rmtree(static_js_dir)
        print(f"Deleted directory: {static_js_dir}")
    else:
        print("static/js directory already gone.")

    # 3. Delete obsolete css files in static/css
    obsolete_css = ["admin_base.css", "admin_stickers.css", "dashboard.css"]
    static_css_dir = os.path.join(backend_app, "static", "css")
    for css_file in obsolete_css:
        path = os.path.join(static_css_dir, css_file)
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted file: {path}")

    # Check if static/css is empty or keep fonts.css
    remaining_css = os.listdir(static_css_dir) if os.path.exists(static_css_dir) else []
    print(f"Remaining files in static/css: {remaining_css}")

    print("Cleanup completed safely.")

if __name__ == "__main__":
    cleanup_legacy_frontend()
