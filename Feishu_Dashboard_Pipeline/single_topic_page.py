#!/usr/bin/env python3
"""Extract the fixed instruction slide plus one topic slide from the HTML PPT.

Usage:
  python3 single_topic_page.py "课题9：打造数字化营销矩阵"
  python3 single_topic_page.py "AI 数字化员工" --output artifacts/topic-10.html
  python3 single_topic_page.py --list

Feishu Aily should resolve the user's free-form message to one concrete topic
first, then pass the exact topic parameter to this script. This script does not
do fuzzy keyword matching such as "AI" -> "课题10：AI 数字化员工".
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SOURCE = Path(__file__).with_name("artifacts") / "创新管理委员会会议材料.html"
FALLBACK_SOURCE = Path(__file__).with_name("创新管理委员会会议材料.html")
DEFAULT_OUTPUT_DIR = Path(__file__).with_name("artifacts") / "single_topics"


@dataclass(frozen=True)
class TopicSlide:
    slide_no: int
    topic_no: int
    title: str
    section_html: str


def normalize(value: str) -> str:
    """Normalize exact topic parameters for punctuation/space tolerance."""
    value = value.lower()
    value = value.replace("“", "").replace("”", "").replace('"', "")
    value = value.replace("：", ":")
    return re.sub(r"[\s\-_·,，。.:：/\\|()（）【】\[\]]+", "", value)


def read_source(path: Path | None = None) -> tuple[Path, str]:
    source = path or (DEFAULT_SOURCE if DEFAULT_SOURCE.exists() else FALLBACK_SOURCE)
    if not source.exists():
        raise FileNotFoundError(f"找不到 HTML PPT 文件：{source}")
    return source, source.read_text(encoding="utf-8")


def split_html_document(source_html: str) -> tuple[str, str, str]:
    match = re.search(
        r"(?s)(.*?<div class=\"deck\" id=\"deck\">\s*)(.*?)(\s*<div class=\"controls\">.*)",
        source_html,
    )
    if not match:
        raise ValueError("无法识别 HTML PPT 结构：没有找到 deck 和 controls 边界")
    return match.group(1), match.group(2), match.group(3)


def extract_sections(deck_html: str) -> list[str]:
    sections = re.findall(r"(?s)<section\b.*?</section>", deck_html)
    if not sections:
        raise ValueError("无法识别任何幻灯片 section")
    return sections


def find_slide_section(source_html: str, slide_no: int) -> str:
    _, deck_html, _ = split_html_document(source_html)
    for section in extract_sections(deck_html):
        slide_match = re.search(r'data-slide="(\d+)"', section)
        if slide_match and int(slide_match.group(1)) == slide_no:
            return section
    raise ValueError(f"没有找到固定第 {slide_no} 页")


def discover_topic_slides(source_html: str) -> list[TopicSlide]:
    _, deck_html, _ = split_html_document(source_html)
    topics: list[TopicSlide] = []
    for section in extract_sections(deck_html):
        slide_match = re.search(r'data-slide="(\d+)"', section)
        title_match = re.search(
            r'<h1 class="detail-title">\s*课题\s*(\d+)\s*[：:]\s*(.*?)\s*</h1>',
            section,
            flags=re.S,
        )
        if not slide_match or not title_match:
            continue
        title = re.sub(r"<[^>]+>", "", title_match.group(2))
        title = html.unescape(re.sub(r"\s+", " ", title)).strip()
        topics.append(
            TopicSlide(
                slide_no=int(slide_match.group(1)),
                topic_no=int(title_match.group(1)),
                title=title,
                section_html=section,
            )
        )
    if not topics:
        raise ValueError("没有找到课题详情页，预期标题格式类似：课题10：AI 数字化员工")
    return topics


def topic_keys(topic: TopicSlide) -> set[str]:
    return {
        normalize(topic.title),
        normalize(f"课题{topic.topic_no}{topic.title}"),
        normalize(f"课题{topic.topic_no}：{topic.title}"),
    }


def match_topic(query: str, topics: list[TopicSlide]) -> TopicSlide:
    normalized_query = normalize(query)
    if not normalized_query:
        raise ValueError("请输入明确课题名称，例如：课题9：打造数字化营销矩阵")

    for topic in topics:
        if normalized_query in topic_keys(topic):
            return topic

    available = "\n".join(f"- 课题{topic.topic_no}：{topic.title}" for topic in topics)
    raise ValueError(f"没有找到这个明确课题：{query}\n请让飞书 Aily 传入以下完整课题之一：\n{available}")


def build_single_page(source_html: str, topic: TopicSlide) -> str:
    prefix, _, suffix = split_html_document(source_html)
    instruction_section = find_slide_section(source_html, 3)
    suffix = re.sub(r"<script>.*?</script>", two_page_script(), suffix, flags=re.S)
    suffix = re.sub(
        r'<div class="counter"><span id="currentSlide">1</span> / <span id="totalSlides">13</span></div>',
        '<div class="counter"><span id="currentSlide">1</span> / <span id="totalSlides">2</span></div>',
        suffix,
    )
    suffix = suffix.replace('<div class="hint">← → 翻页</div>', '<div class="hint">← → 查看指示与课题页</div>')
    return f"{prefix}\n{instruction_section}\n{topic.section_html}\n{suffix}"


def two_page_script() -> str:
    return """<script>
let currentSlide = 1;
const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;
const progressBar = document.getElementById('progressBar');
const hint = document.querySelector('.hint');
const dotsContainer = document.getElementById('dots');

for (let i = 1; i <= totalSlides; i++) {
  const dot = document.createElement('div');
  dot.className = 'dot' + (i === 1 ? ' active' : '');
  dot.onclick = () => goToSlide(i);
  dotsContainer.appendChild(dot);
}

function updateSlide() {
  slides.forEach((slide, index) => {
    slide.classList.remove('active');
    if (index + 1 === currentSlide) slide.classList.add('active');
  });
  document.querySelectorAll('.dot').forEach((dot, index) => {
    dot.classList.toggle('active', index + 1 === currentSlide);
  });
  if (progressBar) progressBar.style.width = ((currentSlide / totalSlides) * 100) + '%';
  document.getElementById('currentSlide').textContent = currentSlide;
  document.getElementById('totalSlides').textContent = totalSlides;
  document.getElementById('prevBtn').disabled = currentSlide === 1;
  document.getElementById('nextBtn').disabled = currentSlide === totalSlides;
}

function nextSlide() { if (currentSlide < totalSlides) { currentSlide++; updateSlide(); } }
function prevSlide() { if (currentSlide > 1) { currentSlide--; updateSlide(); } }
function goToSlide(n) { currentSlide = n; updateSlide(); }

document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'ArrowDown') { e.preventDefault(); nextSlide(); }
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); prevSlide(); }
  else if (e.key === 'Home') goToSlide(1);
  else if (e.key === 'End') goToSlide(totalSlides);
  else if (e.key === 'f' || e.key === 'F') {
    if (!document.fullscreenElement) { document.documentElement.requestFullscreen().catch(()=>{}); }
    else { document.exitFullscreen().catch(()=>{}); }
  }
});

function updateScale() {
  const stage = document.getElementById('deckStage');
  const scaleX = window.innerWidth / 1600;
  const scaleY = window.innerHeight / 900;
  const scale = Math.min(scaleX, scaleY, 1);
  stage.style.setProperty('--stage-scale', scale);
}

window.addEventListener('resize', updateScale);
updateScale();
updateSlide();
setTimeout(() => { if (hint) hint.style.opacity = '0'; }, 3000);
</script>"""


def default_output_path(topic: TopicSlide) -> Path:
    return DEFAULT_OUTPUT_DIR / f"topic-{topic.topic_no:02d}.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按明确课题名称抽取单页 HTML")
    parser.add_argument("query", nargs="?", help="明确课题名称，例如：课题9：打造数字化营销矩阵")
    parser.add_argument("--source", type=Path, help="完整 HTML PPT 路径")
    parser.add_argument("--output", "-o", type=Path, help="输出 HTML 路径")
    parser.add_argument("--list", action="store_true", help="列出可匹配的课题")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source_path, source_html = read_source(args.source)
        topics = discover_topic_slides(source_html)
        if args.list:
            for topic in topics:
                print(f"课题{topic.topic_no}：{topic.title}")
            return 0
        if not args.query:
            raise ValueError("请提供明确课题名称，或使用 --list 查看课题")

        topic = match_topic(args.query, topics)
        output_path = args.output or default_output_path(topic)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_single_page(source_html, topic), encoding="utf-8")
        print(f"已生成：{output_path}")
        print(f"匹配课题：课题{topic.topic_no}：{topic.title}")
        print(f"来源文件：{source_path}")
        return 0
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
