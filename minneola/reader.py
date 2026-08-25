import html
import re
from html.parser import HTMLParser
from urllib.parse import urljoin
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
SKIP_TAGS = {
    "script", "style", "noscript", "svg", "head", "nav", "header",
    "footer", "aside", "form", "button", "select", "iframe", "video",
    "audio", "canvas", "template", "dialog", "input", "textarea",
}
INLINE_BREAKS = {"p", "div", "section", "article", "main", "li", "tr",
                 "td", "th", "figcaption", "dt", "dd", "table", "figure",
                 "hr", "address", "details", "summary", "label"}
READER_CSS = """
body { background:#fafafa; color:#222; margin:0;
       font:16px/1.7 Georgia,'Segoe UI',serif; }
.page { max-width:680px; margin:0 auto; padding:48px 24px 80px; background:#fff; }
h1 { font-size:28px; line-height:1.3; margin:0 0 20px; }
h2 { font-size:22px; margin:28px 0 10px; }
h3 { font-size:19px; margin:24px 0 8px; }
h4, h5, h6 { font-size:17px; margin:20px 0 8px; }
p { margin:0 0 16px; }
a { color:#0b57d0; text-decoration:none; }
a:hover { text-decoration:underline; }
img { max-width:100%; height:auto; border-radius:4px; margin:8px 0; }
figure { margin:20px 0; }
figcaption { font-size:12px; color:#888; margin-top:4px; }
blockquote { border-left:3px solid #ddd; margin:16px 0; padding:2px 18px; color:#555; }
pre { background:#f4f4f4; padding:12px 14px; border-radius:6px; overflow:auto;
      font-size:13px; line-height:1.5; }
ul, ol { margin:0 0 16px; padding-left:26px; }
li { margin:4px 0; }
hr { border:none; border-top:1px solid #e5e5e5; margin:28px 0; }
"""
class ReaderParser(HTMLParser):
    """Collects readable blocks from a page's HTML."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.blocks = []
        self.skip_depth = 0
        self.buffer = []
        self.link_stack = []
        self.list_stack = []
        self.containers = []
        self.in_title = False
        self.in_pre = False
    def flush(self):
        if not self.buffer:
            return
        segments = self._merge_buffer()
        self.buffer = []
        if not segments:
            return
        if self.containers:
            self.containers[-1]["content"].extend(segments)
        else:
            self.blocks.append({"type": "para", "content": segments})
    def _merge_buffer(self):
        segments = []
        for text, href in self.buffer:
            if not self.in_pre:
                text = re.sub(r"\s+", " ", text)
                if not text:
                    continue
            if segments and segments[-1][1] == href:
                segments[-1][0] += text
            else:
                segments.append([text, href])
        if segments and not self.in_pre:
            segments[0][0] = segments[0][0].lstrip()
            segments[-1][0] = segments[-1][0].rstrip()
        return [segment for segment in segments if segment[0]]
    def open_container(self, block):
        self.flush()
        self.blocks.append(block)
        self.containers.append(block)
    def close_container(self):
        self.flush()
        if self.containers:
            self.containers.pop()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
            return
        if self.skip_depth:
            if tag in SKIP_TAGS:
                self.skip_depth += 1
            return
        if tag in SKIP_TAGS:
            self.skip_depth = 1
            return
        if tag == "img":
            src = attrs.get("src") or attrs.get("data-src") or ""
            if src.startswith(("http", "//", "/", "relative")) or src:
                if not src.startswith("data:"):
                    self.flush()
                    self.blocks.append({"type": "img", "src": src,
                                        "alt": attrs.get("alt", "")})
            return
        if tag == "br":
            self.buffer.append(("\n", None))
            return
        if tag == "hr":
            self.flush()
            self.blocks.append({"type": "hr"})
            return
        if tag == "a":
            href = attrs.get("href")
            if href and not href.startswith(("javascript:", "#")):
                self.link_stack.append(href)
            else:
                self.link_stack.append(None)
            return
        if tag in ("ul", "ol"):
            self.list_stack.append(tag)
            return
        if tag == "li":
            self.open_container({"type": "li",
                                 "ordered": bool(self.list_stack and
                                                 self.list_stack[-1] == "ol"),
                                 "content": []})
            return
        if tag in HEADINGS:
            self.open_container({"type": "heading", "level": HEADINGS[tag],
                                 "content": []})
            return
        if tag == "blockquote":
            self.open_container({"type": "quote", "content": []})
            return
        if tag == "pre":
            self.flush()
            block = {"type": "pre", "content": []}
            self.blocks.append(block)
            self.containers.append(block)
            self.in_pre = True
            return
        if tag in INLINE_BREAKS:
            self.flush()
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
            return
        if self.skip_depth:
            if tag in SKIP_TAGS:
                self.skip_depth -= 1
            return
        if tag == "a":
            if self.link_stack:
                self.link_stack.pop()
            return
        if tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            return
        if tag in ("li", "blockquote") or tag in HEADINGS:
            self.close_container()
            return
        if tag == "pre":
            self.close_container()
            self.in_pre = False
            return
        if tag in INLINE_BREAKS:
            self.flush()
    def handle_data(self, data):
        if self.in_title:
            self.title += data
            return
        if self.skip_depth:
            return
        if data:
            href = self.link_stack[-1] if self.link_stack else None
            self.buffer.append((data, href))
def extract_readable(html_text):
    parser = ReaderParser()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:
        pass
    return {"title": parser.title.strip(), "blocks": parser.blocks}
def _render_segments(segments, base_url):
    parts = []
    for text, href in segments:
        escaped = html.escape(text)
        if href:
            absolute = html.escape(urljoin(base_url, href), quote=True)
            parts.append(f'<a href="{absolute}">{escaped}</a>')
        else:
            parts.append(escaped)
    return "".join(parts)
def render_reader_html(data, base_url):
    body = []
    title = data.get("title") or ""
    if title:
        body.append(f"<h1>{html.escape(title)}</h1>")
    list_buffer = []
    def flush_list():
        if list_buffer:
            tag = "ol" if list_buffer[0][0] else "ul"
            items = "".join(f"<li>{item}</li>" for _, item in list_buffer)
            body.append(f"<{tag}>{items}</{tag}>")
            list_buffer.clear()
    for block in data.get("blocks", []):
        kind = block["type"]
        if kind == "li":
            list_buffer.append((block.get("ordered"),
                                _render_segments(block["content"], base_url)))
            continue
        flush_list()
        if kind == "heading":
            level = min(block.get("level", 2), 6)
            content = _render_segments(block["content"], base_url)
            if content.strip():
                body.append(f"<h{level}>{content}</h{level}>")
        elif kind == "para":
            content = _render_segments(block["content"], base_url)
            if content.strip():
                body.append(f"<p>{content}</p>")
        elif kind == "quote":
            content = _render_segments(block["content"], base_url)
            if content.strip():
                body.append(f"<blockquote><p>{content}</p></blockquote>")
        elif kind == "pre":
            content = html.escape("".join(text for text, _ in block["content"]))
            if content.strip():
                body.append(f"<pre>{content}</pre>")
        elif kind == "img":
            src = urljoin(base_url, block.get("src", ""))
            alt = html.escape(block.get("alt", ""), quote=True)
            body.append(f'<figure><img src="{html.escape(src, quote=True)}" '
                        f'alt="{alt}" loading="lazy">'
                        f"{f'<figcaption>{alt}</figcaption>' if alt else ''}"
                        "</figure>")
        elif kind == "hr":
            body.append("<hr>")
    flush_list()
    safe_title = html.escape(title or "Reader view")
    base_tag = html.escape(base_url, quote=True)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{safe_title}</title><base href="{base_tag}">
<style>{READER_CSS}</style></head>
<body><div class="page">{''.join(body)}</div></body></html>"""