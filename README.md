# 🖼️ File-to-Image Converter

> Transform any file into an image and back again with pixel-perfect accuracy

## ✨ Overview

File-to-Image is a unique encoding tool that converts any file into a PNG image by storing the file's binary data as pixel RGB values. Each group of three bytes becomes one pixel, creating a visual representation of your data that can be perfectly restored.

## 🎯 How It Works

### Encoding Process
1. **Header Creation**: Generates a 500-byte header containing the original filename and file size
2. **Binary Reading**: Reads the file's raw binary data and converts it to numerical values
3. **Pixel Mapping**: Groups bytes in sets of three to match RGB color format
4. **Image Generation**: Creates a PNG image where each pixel represents three bytes of data

### Decoding Process
The decoder reverses this process to perfectly reconstruct the original file.

## 🚀 Quick Start

### Prerequisites
- Python 3.x
- PIL (Pillow) library

### Installation
```bash
pip install pillow
```

### Usage

#### Encode a file to image
```bash
python app.py -e path/to/your/file.ext
```

#### Decode image back to file
```bash
python app.py -d
```
*Note: Place the encoded image as `res.png` in the same directory as the decoder*

## 📊 Visual Example

Here's what an encoded file looks like:

![Example encoded image](https://github.com/xhxhkxh/File-to-img/blob/main/example/res.png?raw=true)

### Image Structure Breakdown
- **🌈 Colorful strips (left)**: File header containing metadata
- **⚫ Black area (middle)**: Reserved space for the 500-byte header section  
- **🎨 Large colorful area**: The actual file data encoded as pixels
- **⚫ Black area (bottom)**: Padding to maintain square image dimensions

## ⚠️ Important Notes

- **Filename Length**: Keep filenames reasonably short as they're stored in the 500-byte header
- **Image Integrity**: Do not resize or modify the encoded image - this will corrupt the data and cause decoding errors
- **File Size**: Encoded images will be larger than the original file due to the header and padding requirements

## 🔧 Technical Details

- Header size: Fixed at 500 bytes
- Encoding format: RGB (3 bytes per pixel)
- Output format: PNG
- Image dimensions: Square (calculated based on data size)

## 📈 Size Impact

The tool will display the file size expansion during encoding:
- Original file size → Encoded size (including header)
- Percentage increase
- Final image dimensions

## ⚡ Command Reference

```bash
# Encode mode
python app.py -e [file_path]

# Decode mode (reads res.png automatically)
python app.py -d

# Help
python app.py
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📝 License

This project is open source and available under standard licensing terms.

---

*Built with Python and PIL • Store any file as a beautiful image* 🎨
