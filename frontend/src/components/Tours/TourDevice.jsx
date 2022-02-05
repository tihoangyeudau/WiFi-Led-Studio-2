import { useState } from 'react';
import { MenuItem, ListItemIcon, Badge } from '@material-ui/core';
import Tour from 'reactour';
import { InfoRounded } from '@material-ui/icons';
import useStore from '../../utils/apiStore';

const steps = [
  {
    selector: '.step-device-one',
    content: (
      <div>
        <h2>Loại hiệu ứng</h2>
        Chọn một hiệu ứng ở đây.
        <ul style={{ paddingLeft: '1rem' }}>
          <li>CƠ BẢN: Hiệu ứng đơn giản, không nháy theo nhạc</li>
          <li>1.0: Hiệu ứng nháy theo nhạc</li>
          <li>2D: Hiệu ứng [WIP] được thiết kế cho ma trận LED 2D</li>
          <li>BPM: Các hiệu ứng được thiết kế cho nhịp điệu âm nhạc của bạn</li>
          <li>2.0: Thử nghiệm hiệu ứng nháy theo nhạc mới</li>
        </ul>
        <li>Mỗi hiệu ứng có nhiều cài đặt để dùng</li>
        <li>Bạn có thể điều chỉnh các hiệu ứng theo ý thích của mình</li>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-device-two',
    content: (
      <div>
        <h2>Chuyển tiếp</h2>
        <li>Bạn có thể điều chỉnh hoạt ảnh giữa các hiệu ứng</li>
        <li>Đặt thành 0 để không có hoạt ảnh</li>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-device-three',
    content: (
      <div>
        <h2>Cài trước</h2>
        Dễ dàng lưu và áp dụng các cài đặt của một hiệu ứng.
        WiFi Led Studio có một số cài trước được tích hợp sẵn và bạn cũng có thể lưu của riêng mình
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-device-four',
    content: (
      <div>
        <h2>Dải tần số</h2>
        <li>Điều chỉnh dải tần số âm thanh được sử dụng cho các hiệu ứng</li>
        <li>Hầu hết các hiệu ứng 1.0 sẽ hoạt động với bất kỳ dải tần số nào bạn chỉ định</li>
        <li>Một số hiệu ứng sẽ bỏ qua điều này và thực hiện phân tích nội bộ của riêng chúng</li>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-device-five',
    content: (
      <div>
        <h2>Xoá hiệu ứng</h2>
        Xoá hiệu ứng và ngắt kết nối với đèn
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-device-six',
    content: (
      <div>
        <h2>Ngẫu nhiên</h2>
        Chạy hiệu ứng ngẫu nhiên
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-device-seven',
    content: (
      <div>
        <h2>Hướng dẫn sử dụng hiệu ứng</h2>
        Mỗi hiệu ứng đều có một chuyến tham quan riêng lẻ để giải thích các thuộc tính khác nhau
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
];

const TourDevice = ({ cally }) => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const setTour = useStore((state) => state.setTour);
  const invisible = useStore((state) => state.tours.device);

  return (
    <>
      <MenuItem onClick={(e) => { 
        setIsTourOpen(true); 
        cally(e);
        setTour("device");
        }}>
        <ListItemIcon>
          <Badge variant="dot" color="primary" invisible={invisible}>
            <InfoRounded />
          </Badge>
        </ListItemIcon>
        Hướng dẫn
      </MenuItem>
      <Tour
        steps={steps}
        accentColor="#800000"
        isOpen={isTourOpen}
        onRequestClose={() => setIsTourOpen(false)}
      />
    </>
  );
};

export default TourDevice;
