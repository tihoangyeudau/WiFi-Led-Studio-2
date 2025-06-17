# Global Hotkeys - WiFi Led Studio 2

WiFi Led Studio 2 hỗ trợ các phím tắt toàn cục để điều khiển nhanh các chức năng mà không cần mở giao diện.

## Danh sách phím tắt mặc định

### Điều khiển cơ bản
- **Ctrl+Alt+L**: Bật/tắt LED
- **Ctrl+Alt+S**: Chuyển sang chế độ mở rộng màn hình
- **Ctrl+Alt+W**: Mở giao diện web

### Điều khiển độ sáng
- **Ctrl+Alt+↑**: Tăng độ sáng 10%
- **Ctrl+Alt+↓**: Giảm độ sáng 10%

### Điều khiển hiệu ứng
- **Ctrl+Alt+→**: Chuyển sang hiệu ứng tiếp theo
- **Ctrl+Alt+←**: Chuyển về hiệu ứng trước đó

### Hiệu ứng nhanh
- **Ctrl+Alt+1**: Hiệu ứng Rainbow
- **Ctrl+Alt+2**: Hiệu ứng Strobe
- **Ctrl+Alt+3**: Hiệu ứng Fade
- **Ctrl+Alt+4**: Hiệu ứng Energy

## Bật/tắt phím tắt

Bạn có thể bật/tắt phím tắt toàn cục thông qua:
1. Nhấp chuột phải vào biểu tượng trong system tray
2. Chọn **Bật/Tắt phím tắt toàn cục** (ngay sau menu khởi động)

## Yêu cầu quyền truy cập

### Windows
- Không cần cấu hình đặc biệt
- Phím tắt hoạt động ngay lập tức

### macOS
- Cần cấp quyền **Accessibility** cho Python hoặc Terminal
- Đi tới **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
- Thêm Python executable hoặc Terminal vào danh sách ứng dụng được phép

## 🎛️ Tùy chỉnh phím tắt

**📖 Hướng dẫn chi tiết**: [HOTKEY_CUSTOMIZATION.md](HOTKEY_CUSTOMIZATION.md)

Bạn có thể tùy chỉnh hoàn toàn các phím tắt thông qua file cấu hình. Ví dụ:

```json
{
  "hotkey_settings": {
    "enabled": true,
    "mappings": {
      "<ctrl>+<shift>+<up>": "increase_brightness",
      "<ctrl>+<shift>+<down>": "decrease_brightness",
      "<f1>": "quick_effect_rainbow",
      "<win>+l": "toggle_led_state"
    }
  }
}
```

### Các hành động có sẵn
- `toggle_led_state`, `increase_brightness`, `decrease_brightness`
- `next_effect`, `previous_effect`
- `quick_effect_rainbow`, `quick_effect_strobe`, `quick_effect_fade`, `quick_effect_energy`
- `screen_capture`, `open_web_interface`

## Xử lý sự cố

### Phím tắt không hoạt động
1. Kiểm tra xem phím tắt có được bật trong menu không
2. Trên macOS, kiểm tra quyền Accessibility
3. Kiểm tra log để xem có lỗi nào không

### Xung đột phím tắt
- Nếu phím tắt bị xung đột với ứng dụng khác, hãy thay đổi tổ hợp phím
- Tránh sử dụng các phím tắt hệ thống phổ biến

### Hiệu suất
- Phím tắt toàn cục có thể ảnh hưởng nhẹ đến hiệu suất
- Nếu gặp vấn đề, có thể tắt tính năng này

## Ghi chú kỹ thuật

- Sử dụng thư viện `pynput` cho tính năng cross-platform
- Phím tắt chạy trong thread riêng biệt để không ảnh hưởng đến hiệu suất chính
- Tự động xử lý lỗi và ghi log chi tiết