# Ultimate Image Converter AI &nbsp;`v3.1.0`

A professional desktop image processing application built with Python and Tkinter. Designed for batch image conversion, AI-powered upscaling, background removal, non-destructive editing, and smart export — all in one workflow.

---

## Features

### 🖼 Converter
- Batch convert images to **JPG, PNG, WEBP, BMP**
- Smart border modes: **solid color**, **blurred background**, **dominant color fill**
- Built-in presets for social media and print formats (Instagram, Twitter, YouTube, A4, 4K, and more)
- Custom output dimensions with optional original size preservation
- EXIF metadata stripping

### 🤖 AI Tools
- **Background removal** powered by [rembg](https://github.com/danielgatis/rembg)
- **AI upscaling** via Real-ESRGAN ONNX models
  - `Low` mode — 2× upscale (RealESRGAN x2plus)
  - `Balanced` mode — 4× upscale (RealESRGAN x4plus)
  - `Ultra` mode — 4× upscale (RealESRGAN x4plus, GPU path reserved for future)
  - Automatic Lanczos fallback if model is unavailable

### ✂ Editor
- Non-destructive adjustments: **brightness, contrast, saturation, sharpness**
- Filters: **Grayscale, Sepia, Vivid, Cool, Warm, Vintage**
- Rotate (90°/180°/270°) and flip (horizontal/vertical)
- Crop with normalized or pixel coordinates
- Text and logo **watermark** support with opacity and position control
- **Color palette extraction** from any image

### 📦 Batch & Export
- Process hundreds of images in one run
- Custom **rename patterns** (`{name}`, `{date}`, `{index}`, etc.)
- Target file size optimization
- Folder watch mode — auto-process new files as they arrive
- Progress tracking with per-file logging

### ⚙ Settings
- Dark / Light theme (+ Purple, Ocean, Forest)
- Persistent settings via `settings.json`
- Preset save/load system
- Configurable output folder, quality, format, and border defaults
- Created by **Riindewin**

---

## Screenshots

> Add screenshots here after first stable release.

---

## Requirements

- Python 3.10+
- Windows / macOS / Linux

### Dependencies

```
Pillow>=10.0.0
tkinterdnd2>=0.3.0
onnxruntime>=1.16.0
numpy>=1.24.0
rembg>=2.0.0
pytest>=8.0.0
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/Riindewin/Ai-Workflow.git
cd Ai-Workflow

# 2. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

On Windows you can also use the included launcher:

```bash
run.bat
```

---

## Project Structure

```
Ai-Workflow/
├── app.py                  # Entry point
├── settings.json           # User settings (auto-generated)
├── requirements.txt
│
├── core/                   # Business logic
│   ├── ai_engine.py        # Real-ESRGAN upscaling + Lanczos fallback
│   ├── color_palette.py    # Dominant color extraction
│   ├── converter.py        # Batch image conversion pipeline
│   ├── export_engine.py    # File save with format/quality/EXIF handling
│   ├── exif_reader.py      # EXIF metadata reader
│   ├── file_size_optimizer.py
│   ├── image_editor.py     # Non-destructive editing operations
│   ├── preview_engine.py   # Live preview rendering
│   ├── smart_border.py     # Blur / dominant / solid background builder
│   ├── theme_engine.py     # UI theme management
│   └── watermark_engine.py # Text and logo watermarking
│
├── models/                 # ONNX model files (auto-downloaded on first use)
│
├── services/               # Application services
│   ├── logger_service.py
│   ├── model_manager.py    # ONNX model download and caching
│   ├── preset_service.py   # Preset save/load
│   ├── rembg_service.py    # Background removal service
│   ├── settings_service.py # Settings persistence
│   └── watch_service.py    # Folder watch service
│
├── ui/                     # User interface
│   ├── main_window.py
│   ├── dialogs/            # Keyboard shortcuts, color/font pickers
│   ├── panels/             # File panel, preview, settings, log, zoom/pan canvas
│   ├── tabs/               # Converter, AI, Editor, Batch, Settings, Info tabs
│   └── widgets/            # Reusable widgets (toast, split button)
│
├── utils/                  # Utilities
│   ├── constants.py        # App-wide constants and theme palette
│   ├── i18n.py             # Internationalization
│   ├── image_processor.py  # Image composition helpers
│   ├── rename_helper.py    # Rename pattern engine
│   └── themes.py           # Theme definitions
│
├── models/                 # App state
│   └── app_state.py
│
└── tests/                  # Test suite
    ├── test_ai_engine.py
    ├── test_image_processor.py
    ├── test_settings_service.py
    └── test_smart_border.py
```

---

## Running Tests

```bash
pytest tests/
```

---

## Built-in Presets

| Preset            | Width  | Height | Format |
|-------------------|--------|--------|--------|
| Instagram Square  | 1080   | 1080   | JPG    |
| Instagram Story   | 1080   | 1920   | JPG    |
| Twitter Banner    | 1500   | 500    | JPG    |
| Twitter Post      | 1200   | 675    | JPG    |
| Facebook Cover    | 820    | 312    | JPG    |
| YouTube Thumbnail | 1280   | 720    | JPG    |
| Print A4          | 2480   | 3508   | PNG    |
| Print A5          | 1748   | 2480   | PNG    |
| Wallpaper FHD     | 1920   | 1080   | JPG    |
| Wallpaper 4K      | 3840   | 2160   | JPG    |

---

## AI Models

Models are downloaded automatically on first use and cached in the `models/` folder.

| Mode     | Model               | Scale | Size   |
|----------|---------------------|-------|--------|
| Low      | RealESRGAN_x2plus   | 2×    | ~65 MB |
| Balanced | RealESRGAN_x4plus   | 4×    | ~65 MB |
| Ultra    | RealESRGAN_x4plus   | 4×    | ~65 MB (GPU path reserved for future) |

If a model cannot be downloaded, the engine automatically falls back to high-quality **Lanczos** interpolation.

---

## License

This project is currently unlicensed. All rights reserved.

---

## Author

**Riindewin** — [github.com/Riindewin](https://github.com/Riindewin)
