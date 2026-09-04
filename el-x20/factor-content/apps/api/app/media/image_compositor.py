"""Compositor de fotos — reemplaza a ffmpeg_runner.py como motor de render
tras el pivote vídeo->foto. Usa Pillow: no reinventamos un editor de
imágenes, solo orquestamos composición determinista sobre una plantilla
data-driven (mismo principio que el spec pedía para FFmpeg en vídeo).

El texto real de cada zona (hook, cta, title...) lo produce ai_service.py;
este módulo solo dibuja lo que recibe, en las coordenadas/estilo que
define la plantilla."""
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont


class CompositorError(Exception):
    pass


@dataclass
class ImageInfo:
    width: int
    height: int
    format: str


def probe(input_path: str) -> ImageInfo:
    """Metadata técnica de la imagen — reemplaza a ffprobe para fotos."""
    with Image.open(input_path) as img:
        return ImageInfo(width=img.width, height=img.height, format=(img.format or "").lower())


def _fit_to_canvas(img: Image.Image, width: int, height: int, mode: str) -> Image.Image:
    src_ratio = img.width / img.height
    dst_ratio = width / height

    if mode == "cover":
        if src_ratio > dst_ratio:
            new_h = height
            new_w = int(height * src_ratio)
        else:
            new_w = width
            new_h = int(width / src_ratio)
        resized = img.resize((new_w, new_h))
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return resized.crop((left, top, left + width, top + height))

    # contain: encajar sin recortar, rellenar el resto en negro
    if src_ratio > dst_ratio:
        new_w = width
        new_h = int(width / src_ratio)
    else:
        new_h = height
        new_w = int(height * src_ratio)
    resized = img.resize((new_w, new_h))
    canvas = Image.new("RGB", (width, height), (0, 0, 0))
    canvas.paste(resized, ((width - new_w) // 2, (height - new_h) // 2))
    return canvas


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_zone(draw: ImageDraw.ImageDraw, zone: dict, text: str, font_path: str | None) -> None:
    if not text:
        return
    font_size = zone.get("font_size", 48)
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default(font_size)
    except OSError:
        font = ImageFont.load_default(font_size)

    max_width = zone["max_width"]
    lines = _wrap_text(draw, text, font, max_width)
    line_height = font_size + 8
    total_height = line_height * len(lines)

    x, y = zone["x"], zone["y"]
    align = zone.get("align", "center")
    style = zone.get("style", "box")

    if style == "box" and zone.get("box_enabled", True):
        box_color = zone.get("box_color", "#000000")
        opacity = int(zone.get("box_opacity", 0.55) * 255)
        rgb = tuple(int(box_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        overlay = Image.new("RGBA", (max_width + 40, total_height + 30), (*rgb, opacity))
        draw._image.paste(overlay, (x - 20, y - 15), overlay)  # noqa: SLF001

    outline_kwargs = {}
    if style == "outline":
        outline_kwargs = {
            "stroke_width": zone.get("outline_width", 3),
            "stroke_fill": zone.get("outline_color", "#000000"),
        }

    for i, line in enumerate(lines):
        line_width = draw.textlength(line, font=font)
        if align == "center":
            line_x = x + (max_width - line_width) / 2
        elif align == "right":
            line_x = x + max_width - line_width
        else:
            line_x = x
        draw.text(
            (line_x, y + i * line_height), line, fill=zone.get("font_color", "#FFFFFF"), font=font,
            **outline_kwargs,
        )


def _draw_bubble_list(
    draw: ImageDraw.ImageDraw, zone: dict, texts: list[str], font_path: str | None
) -> None:
    """Dibuja N burbujas de chat apiladas verticalmente, una por texto,
    empezando en zone['y'] y creciendo hacia abajo. Formato tipo mensajería
    (rectángulo redondeado + texto centrado), como en el ejemplo del
    operador: cada 'beat' del guion es una burbuja independiente."""
    if not texts:
        return

    font_size = zone.get("font_size", 42)
    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default(font_size)
    except OSError:
        font = ImageFont.load_default(font_size)

    max_width = zone["max_width"]
    x = zone["x"]
    y = zone["y"]
    spacing = zone.get("spacing", 24)
    corner_radius = zone.get("corner_radius", 30)
    align = zone.get("align", "center")

    bubble_color = zone.get("bubble_color", "#4A4A4A")
    opacity = int(zone.get("bubble_opacity", 0.85) * 255)
    rgb = tuple(int(bubble_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))

    for text in texts:
        if not text:
            continue
        lines = _wrap_text(draw, text, font, max_width - 60)  # padding interno de la burbuja
        line_height = font_size + 10
        text_height = line_height * len(lines)
        bubble_height = text_height + 50

        draw.rounded_rectangle(
            (x, y, x + max_width, y + bubble_height), radius=corner_radius, fill=(*rgb, opacity),
        )

        for i, line in enumerate(lines):
            line_width = draw.textlength(line, font=font)
            if align == "center":
                line_x = x + (max_width - line_width) / 2
            elif align == "right":
                line_x = x + max_width - 30 - line_width
            else:
                line_x = x + 30
            draw.text(
                (line_x, y + 25 + i * line_height), line,
                fill=zone.get("font_color", "#FFFFFF"), font=font,
            )

        y += bubble_height + spacing


def compose(
    *,
    input_path: str,
    output_path: str,
    config: dict,
    zone_texts: dict[str, str | list[str]],
    logo_path: str | None = None,
    font_path: str | None = None,
) -> None:
    """Compone la foto final: fit al canvas + zonas de texto simple +
    listas de burbujas + branding.

    zone_texts: {"hook": "...", "cta": "..."} para zones simples, o
    {"body_beats": ["...", "...", "..."]} para bubble_lists — la key debe
    corresponder al role de la zona/lista correspondiente. Roles ausentes
    (o enabled=False) se omiten silenciosamente, nunca bloquean el render.
    """
    canvas_cfg = config["canvas"]
    width, height = canvas_cfg["width"], canvas_cfg["height"]

    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            base = _fit_to_canvas(img, width, height, canvas_cfg.get("background_fit", "cover"))
    except Exception as exc:  # noqa: BLE001
        raise CompositorError(f"No se pudo abrir/ajustar la imagen de entrada: {exc}") from exc

    draw = ImageDraw.Draw(base, "RGBA")

    for zone in config.get("zones", []):
        if not zone.get("enabled", True):
            continue
        text = zone_texts.get(zone["role"], "")
        if isinstance(text, list):
            continue  # una lista no pertenece a una zone simple, se ignora aquí
        _draw_zone(draw, zone, text, font_path)

    for bubble_zone in config.get("bubble_lists", []):
        if not bubble_zone.get("enabled", True):
            continue
        texts = zone_texts.get(bubble_zone["role"], [])
        if isinstance(texts, str):
            texts = [texts]  # tolerante: un solo string se trata como lista de 1
        _draw_bubble_list(draw, bubble_zone, texts, font_path)

    branding = config.get("branding", {})
    if branding.get("enabled") and logo_path:
        try:
            with Image.open(logo_path) as logo:
                logo = logo.convert("RGBA")
                margin = 40
                positions = {
                    "top-left": (margin, margin),
                    "top-right": (width - logo.width - margin, margin),
                    "bottom-left": (margin, height - logo.height - margin),
                    "bottom-right": (width - logo.width - margin, height - logo.height - margin),
                }
                pos = positions.get(branding.get("position", "bottom-right"), positions["bottom-right"])
                base.paste(logo, pos, logo)
        except Exception as exc:  # noqa: BLE001
            raise CompositorError(f"No se pudo componer el logo de branding: {exc}") from exc

    output_cfg = config.get("output", {"format": "jpg", "quality": 90})
    fmt = output_cfg.get("format", "jpg")
    if fmt == "jpg":
        base.save(output_path, format="JPEG", quality=output_cfg.get("quality", 90))
    else:
        base.save(output_path, format="PNG")
