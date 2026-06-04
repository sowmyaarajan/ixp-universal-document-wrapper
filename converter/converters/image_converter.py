import logging
from pathlib import Path

from converter.converters.base_converter import BaseConverter
from converter.exceptions import CorruptedFileError, ConversionError

logger = logging.getLogger(__name__)


class ImageConverter(BaseConverter):

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}

    def convert(self, input_path: Path, output_path: Path) -> Path:
        self._validate_input(input_path)
        try:
            from PIL import Image, UnidentifiedImageError
        except ImportError:
            raise ConversionError("Pillow is not installed. Run: pip install Pillow")

        logger.info("Converting image %s -> %s", input_path, output_path)
        try:
            img = Image.open(input_path)
            frames = self._collect_frames(img)
        except Exception as e:
            raise CorruptedFileError(f"Cannot open image {input_path}: {e}") from e

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if len(frames) == 1:
                frames[0].save(str(output_path), format="PDF", resolution=150)
            else:
                frames[0].save(
                    str(output_path),
                    format="PDF",
                    resolution=150,
                    save_all=True,
                    append_images=frames[1:],
                )
        except Exception as e:
            raise ConversionError(f"Failed to write PDF from {input_path}: {e}") from e

        logger.info("Image conversion complete: %s", output_path)
        return output_path

    def _collect_frames(self, img) -> list:
        from PIL import Image

        frames = []
        try:
            while True:
                frame = self._to_rgb(img.copy())
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        return frames if frames else [self._to_rgb(img)]

    @staticmethod
    def _to_rgb(img) -> "Image":
        from PIL import Image as PILImage
        if img.mode in ("RGBA", "LA", "P"):
            background = PILImage.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            return background
        if img.mode != "RGB":
            return img.convert("RGB")
        return img
