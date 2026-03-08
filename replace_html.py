import re

def process_html(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()

    # まず、すでにある <span style="display:inline-block;"> を削除してクリーンにする
    html = re.sub(r'<span style="display:inline-block;">(.*?)</span>', r'\1', html)
    
    # 対象のタグ
    tags = ['p', 'span', 'h1', 'h2', 'h3', 'li', 'div', 'button', 'a', 'ul']

    def apply_class(m):
        tag_match = m.group(1).lower()
        if tag_match not in tags:
            return m.group(0)

        attrs = m.group(2)
        
        # 閉じタグや自己完結タグの場合は無視
        if m.group(0).startswith('</') or attrs.strip().endswith('/'):
            return m.group(0)

        if 'class=' in attrs:
            # 既に class がある場合
            class_match = re.search(r'class=[\"\']([^\"\']*)[\"\']', attrs)
            if class_match:
                classes = class_match.group(1).split()
                if 'keep-all' not in classes:
                    classes.append('keep-all')
                    new_attrs = attrs.replace(class_match.group(0), f'class="{" ".join(classes)}"')
                    return f'<{m.group(1)}{new_attrs}>'
            return m.group(0)
        else:
            # classがない場合は追加
            return f'<{m.group(1)} class="keep-all"{attrs}>'

    # 開きタグにマッチ
    new_html = re.sub(r'<([a-zA-Z0-9\-]+)([^>]*)>', apply_class, html)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print('done')

if __name__ == '__main__':
    process_html('index.html')
