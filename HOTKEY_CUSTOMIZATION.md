# Tùy chỉnh phím tắt toàn cục (Global Hotkeys)

WiFi Led Studio 2 cho phép bạn tùy chỉnh các phím tắt toàn cục thông qua file cấu hình.

## 📍 Vị trí file cấu hình

File cấu hình được lưu tại:
- **Windows**: `C:\Users\[username]\.wls\cau_hinh.json`
- **macOS**: `~/.wls/cau_hinh.json`
- **Linux**: `~/.wls/cau_hinh.json`

## 🎹 Cấu trúc hotkey trong config

```json
{
  "hotkey_settings": {
    "enabled": true,
    "mappings": {
      "<ctrl>+<alt>+l": "toggle_led_state",
      "<ctrl>+<alt>+<up>": "increase_brightness",
      "<ctrl>+<alt>+<down>": "decrease_brightness",
      "<ctrl>+<alt>+<right>": "next_effect",
      "<ctrl>+<alt>+<left>": "previous_effect",
      "<ctrl>+<alt>+1": "quick_effect_rainbow",
      "<ctrl>+<alt>+2": "quick_effect_strobe",
      "<ctrl>+<alt>+3": "quick_effect_fade",
      "<ctrl>+<alt>+4": "quick_effect_energy",
      "<ctrl>+<alt>+s": "screen_capture",
      "<ctrl>+<alt>+w": "open_web_interface"
    }
  }
}
```

## 🔧 Cách tùy chỉnh

### 1. Tắt/Bật hotkeys
```json
"hotkey_settings": {
  "enabled": false  // Tắt tất cả hotkeys
}
```

### 2. Thay đổi phím tắt hiện có
```json
"mappings": {
  "<ctrl>+<shift>+<up>": "increase_brightness",    // Thay đổi từ Ctrl+Alt+Up
  "<ctrl>+<shift>+<down>": "decrease_brightness"   // Thay đổi từ Ctrl+Alt+Down
}
```

### 3. Thêm phím tắt mới
```json
"mappings": {
  "<ctrl>+<alt>+r": "quick_effect_rainbow",        // Thêm phím tắt cho Rainbow
  "<ctrl>+<alt>+t": "toggle_led_state",            // Thêm phím tắt toggle khác
  "<win>+<alt>+s": "screen_capture"                // Sử dụng Windows key
}
```

### 4. Xóa phím tắt
Chỉ cần không đưa phím tắt đó vào `mappings`, nó sẽ không được load.

## 🎯 Các hành động có sẵn (Actions)

| Action | Mô tả |
|--------|-------|
| `toggle_led_state` | Bật/tắt LED |
| `increase_brightness` | Tăng độ sáng 10% |
| `decrease_brightness` | Giảm độ sáng 10% |
| `next_effect` | Chuyển sang hiệu ứng tiếp theo |
| `previous_effect` | Chuyển về hiệu ứng trước |
| `quick_effect_rainbow` | Áp dụng hiệu ứng Rainbow |
| `quick_effect_strobe` | Áp dụng hiệu ứng Strobe |
| `quick_effect_fade` | Áp dụng hiệu ứng Fade |
| `quick_effect_energy` | Áp dụng hiệu ứng Energy |
| `screen_capture` | Bắt đầu chế độ bắt màn hình |
| `open_web_interface` | Mở giao diện web |

## ⌨️ Định dạng phím (Key Format)

### Modifier Keys
- `<ctrl>` - Ctrl key
- `<alt>` - Alt key  
- `<shift>` - Shift key
- `<win>` - Windows key (chỉ Windows)
- `<cmd>` - Command key (chỉ macOS)

### Phím thường
- `<up>`, `<down>`, `<left>`, `<right>` - Phím mũi tên
- `<space>` - Phím space
- `<enter>` - Phím Enter
- `<tab>` - Phím Tab
- `<esc>` - Phím Escape
- `a`, `b`, `c`, ... - Các chữ cái
- `1`, `2`, `3`, ... - Các số
- `<f1>`, `<f2>`, ... `<f12>` - Function keys

### Ví dụ tổ hợp phím
```json
"<ctrl>+<alt>+<space>": "toggle_led_state",
"<ctrl>+<shift>+r": "quick_effect_rainbow",
"<win>+l": "toggle_led_state",
"<f1>": "screen_capture",
"<ctrl>+<alt>+<f5>": "next_effect"
```

## 🔄 Áp dụng thay đổi

Sau khi chỉnh sửa file cấu hình:

1. **Lưu file** `cau_hinh.json`
2. **Khởi động lại** WiFi Led Studio 2
3. Hoặc **Toggle hotkeys** trong system tray menu để reload

## ⚠️ Lưu ý quan trọng

1. **Backup config**: Luôn sao lưu file cấu hình trước khi chỉnh sửa
2. **JSON syntax**: Đảm bảo syntax JSON đúng (dùng JSON validator)
3. **Phím trùng**: Tránh sử dụng phím tắt trùng với hệ thống hoặc ứng dụng khác
4. **Test**: Test phím tắt sau khi thay đổi để đảm bảo hoạt động

## 🛠️ Troubleshooting

### Hotkeys không hoạt động
1. Kiểm tra `"enabled": true` trong config
2. Kiểm tra syntax JSON
3. Kiểm tra log file để xem lỗi
4. Restart ứng dụng

### Phím tắt bị trùng
1. Kiểm tra Task Manager để xem ứng dụng nào đang dùng phím tắt đó
2. Thay đổi tổ hợp phím khác
3. Tắt hotkeys của ứng dụng khác nếu cần

### Khôi phục mặc định
Xóa section `hotkey_settings` trong config hoặc set:
```json
"hotkey_settings": {
  "enabled": true,
  "mappings": {}
}
```

## 📝 Ví dụ cấu hình tùy chỉnh

```json
{
  "hotkey_settings": {
    "enabled": true,
    "mappings": {
      // Brightness controls với Shift thay vì Alt
      "<ctrl>+<shift>+<up>": "increase_brightness",
      "<ctrl>+<shift>+<down>": "decrease_brightness",
      
      // Effect controls với Function keys
      "<f1>": "quick_effect_rainbow",
      "<f2>": "quick_effect_strobe", 
      "<f3>": "quick_effect_fade",
      "<f4>": "quick_effect_energy",
      
      // Toggle với Windows key
      "<win>+l": "toggle_led_state",
      
      // Screen capture với Ctrl+Alt+Print
      "<ctrl>+<alt>+<print>": "screen_capture",
      
      // Web interface với Ctrl+Alt+W
      "<ctrl>+<alt>+w": "open_web_interface"
    }
  }
}
```

Với cấu hình này, bạn có thể tùy chỉnh hoàn toàn các phím tắt theo sở thích và không bị xung đột với các ứng dụng khác!