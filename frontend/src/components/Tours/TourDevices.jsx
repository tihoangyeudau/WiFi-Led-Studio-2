import { useState } from 'react';
import { MenuItem, ListItemIcon, Badge } from '@material-ui/core';
import Tour from 'reactour';
import { InfoRounded } from '@material-ui/icons';
import useStore from '../../utils/apiStore';

const steps = [
  {
    selector: '.step-devices-one',
    content: (
      <div>
        <h2>Quản lý đèn</h2>
        Thêm ít nhất một đèn bằng cách sử dụng nút màu đỏ để xem hướng dẫn cụ thể.
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-devices-two-0',
    content: (
      <div>
        <h2>Mở rộng</h2>
        Nhấp vào mũi tên xuống để chuyển đổi các tùy chọn.
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-devices-three-0',
    content: (
      <div>
        <h2>Xoá</h2>
        Có thể xóa đèn bằng biểu tượng thùng rác.
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-devices-four-0',
    content: (
      <div>
        <h2>Cài đặt đèn</h2>
        Cờ lê sẽ cho phép bạn sửa đổi cài đặt đèn hợp lý bao gồm cả chế độ phát trực tuyến
        , số lượng Led và địa chỉ IP.
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-devices-five-0',
    content: (
      <div>
        <h2>Cài đặt đèn ảo</h2>
        Bánh răng sẽ cho phép bạn thay đổi các cài đặt của đèn ảo khác nhau.
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-devices-six',
    content: (
      <div>
        <h2>Cài đặt phân đoạn</h2>
        Biểu tượng thanh trượt sẽ cho phép bạn sửa đổi các phân đoạn của đèn ảo.
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-devices-seven',
    content: (
      <div>
        <h2>Đồ thị điểm ảnh</h2>
        Khi chủ động phát trực tuyến với nguồn âm thanh đang hoạt động được chọn, bạn sẽ thấy
        biểu đồ hiển thị ở đây.
        <p>
          Lưu ý: Đồ thị bị tắt theo mặc định để giữ an toàn cho các máy cấu hình yếu.
          Đối với các máy khách cấu hình cao, chúng có thể được bật bằng cách sử dụng menu trên cùng bên phải
        </p>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
];

const TourDevices = ({ cally }) => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const setTour = useStore((state) => state.setTour);
  const invisible = useStore((state) => state.tours.devices);
  return (
    <>
      <MenuItem onClick={(e) => { 
        setIsTourOpen(true); 
        cally(e);
        setTour("devices");
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



export default TourDevices;
