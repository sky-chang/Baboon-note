import os
import http.server
import socketserver
from html import escape
import re
import webbrowser
import subprocess
import shutil

def move_txt_files_to_current_folder():
    # 获取当前文件夹路径
    current_folder = os.getcwd()

    # 获取上一级文件夹路径
    parent_folder = os.path.abspath(os.path.join(current_folder, ".."))

    # 遍历上一级文件夹中的所有文件
    for filename in os.listdir(parent_folder):
        file_path = os.path.join(parent_folder, filename)

        # 检查文件是否为txt文件
        if os.path.isfile(file_path) and filename.endswith(".txt"):
            # 将txt文件移动到当前文件夹
            shutil.move(file_path, current_folder)
            print(f"Moved: {filename} to {current_folder}")

if __name__ == "__main__":
    move_txt_files_to_current_folder()

class TextFileHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        folder_path = os.path.dirname(os.path.abspath(__file__))
        files = os.listdir(folder_path)

        html_content = """
        <html>
        <head>
            <title>Baboon随心看</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f0f8ff; }
                h1 { text-align: center; color: #333; animation: fadein 2s; }
                .header { text-align: center; font-size: 1.5em; margin-bottom: 20px; color: #555; }
                .container { display: none; margin-top: 20px; }
                .file { margin-bottom: 20px; border: 1px solid #ddd; border-radius: 5px; padding: 10px; background: #fff; }
                .filename { font-weight: bold; color: #007BFF; cursor: pointer; display: block; }
                .filename:hover { text-decoration: underline; }
                .preview, .content { color: #555; white-space: pre-wrap; word-wrap: break-word; font-size: 16px; line-height: 1.5; }
                .content { display: none; }
                button { margin-top: 10px; background: #007BFF; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .controls { text-align: center; margin-bottom: 20px; }
                .controls button { margin: 0 10px; padding: 10px 20px; }
                #search-box { width: 100%; padding: 10px; margin-bottom: 20px; font-size: 16px; }
                #search-results { margin-top: 20px; }
                .highlight { background-color: yellow; color: black; font-weight: bold; }
                @keyframes fadein {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
            </style>
            <script>
                function toggleSection(sectionId) {
                    document.querySelectorAll('.container').forEach(container => {
                        container.style.display = 'none';
                    });
                    document.getElementById(sectionId).style.display = 'block';
                }

                function toggleContent(previewId, contentId, buttonId) {
                    const preview = document.getElementById(previewId);
                    const content = document.getElementById(contentId);
                    const button = document.getElementById(buttonId);

                    if (content.style.display === 'none' || !content.style.display) {
                        preview.style.display = 'none';
                        content.style.display = 'block';
                        button.textContent = '隐藏';
                    } else {
                        content.style.display = 'none';
                        preview.style.display = 'block';
                        button.textContent = '展开';
                    }
                }

                function performSearch() {
                    const searchTerm = document.getElementById('search-box').value.toLowerCase();
                    const searchResultsDiv = document.getElementById('search-results');
                    searchResultsDiv.innerHTML = ''; // 清空搜索结果

                    if (!searchTerm) {
                        searchResultsDiv.style.display = 'none';
                        return;
                    }

                    const allFiles = document.querySelectorAll('.file');
                    const searchResults = [];

                    allFiles.forEach(fileDiv => {
                        const filename = fileDiv.querySelector('.filename').textContent.toLowerCase();
                        const preview = fileDiv.querySelector('.preview').textContent.toLowerCase();

                        if (filename.includes(searchTerm) || preview.includes(searchTerm)) {
                            const clonedDiv = fileDiv.cloneNode(true);

                            // 高亮文件名
                            const clonedFilename = clonedDiv.querySelector('.filename');
                            clonedFilename.innerHTML = clonedFilename.textContent.replace(new RegExp(searchTerm, 'gi'), match => `<span class="highlight">${match}</span>`);

                            // 高亮预览内容
                            const clonedPreview = clonedDiv.querySelector('.preview');
                            clonedPreview.innerHTML = clonedPreview.textContent.replace(new RegExp(searchTerm, 'gi'), match => `<span class="highlight">${match}</span>`);

                            searchResults.push(clonedDiv);
                        }
                    });

                    if (searchResults.length > 0) {
                        searchResultsDiv.style.display = 'block';
                        searchResultsDiv.innerHTML = '<h3>搜索结果：</h3>';
                        searchResults.forEach(result => {
                            searchResultsDiv.appendChild(result);
                        });
                    } else {
                        searchResultsDiv.style.display = 'block';
                        searchResultsDiv.innerHTML = '<p>未找到匹配的文件。</p>';
                    }
                }

                function openFile(filepath) {
                    fetch(`/open-file?file=${encodeURIComponent(filepath)}`)
                        .then(response => {
                            if (!response.ok) {
                                alert("无法打开文件");
                            }
                        });
                }
            </script>
        </head>
        <body>
            <h1>Baboon随心看</h1>
            <input type="text" id="search-box" placeholder="搜索文件名或内容" oninput="performSearch()">
            <div id="search-results"></div>
            <div class="controls">
                <button onclick="toggleSection('date-files')">日记</button>
                <button onclick="toggleSection('excerpt-files')">摘抄</button>
                <button onclick="toggleSection('other-files')">随笔</button>
            </div>
            <div id="date-files" class="container" style="display: block;">
        """

        # 文件分类规则
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}.*\.txt$')
        excerpt_pattern = re.compile(r'^摘抄.*\.txt$', re.IGNORECASE)

        # 获取文本文件
        all_files = []
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(folder_path, file)
                creation_time = os.path.getctime(file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                all_files.append((file, content, creation_time))
        all_files.sort(key=lambda x: x[2], reverse=True)

        # 分类文件
        date_files = [f for f in all_files if date_pattern.match(f[0])]
        excerpt_files = [f for f in all_files if excerpt_pattern.match(f[0])]
        other_files = [f for f in all_files if f not in date_files and f not in excerpt_files]

        # 渲染文件列表
        def render_files(files, section):
            html = ""
            for i, (file, content, _) in enumerate(files):
                preview = escape("\n".join(content.split('\n')[:8]) + ("..." if len(content.split('\n')) > 8 else ""))
                escaped_content = escape(content)
                html += f"""
                <div class="file">
                    <div class="filename" onclick="openFile('{file}')">{file}</div>
                    <div class="preview" id="{section}-preview-{i}">{preview}</div>
                    <div class="content" id="{section}-content-{i}" style="display: none;">{escaped_content}</div>
                    <button id="{section}-button-{i}" onclick="toggleContent('{section}-preview-{i}', '{section}-content-{i}', '{section}-button-{i}')">展开</button>
                </div>
                """
            return html

        html_content += render_files(date_files, "date")
        html_content += "</div><div id='excerpt-files' class='container'>"
        html_content += render_files(excerpt_files, "excerpt")
        html_content += "</div><div id='other-files' class='container'>"
        html_content += render_files(other_files, "other")
        html_content += """
            </div>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def do_POST(self):
        if self.path.startswith("/open-file"):
            query = self.path.split("?file=", 1)[-1]
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), query)
            if os.path.exists(file_path):
                subprocess.run(["notepad", file_path], shell=True)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"File opened")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")

# 启动服务器
PORT = 8080
def run_server():
    with socketserver.TCPServer(("", PORT), TextFileHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()

def open_browser():
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == "__main__":
    open_browser()
    run_server()
