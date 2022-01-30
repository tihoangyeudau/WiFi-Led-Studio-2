import { useLayoutEffect, useState } from 'react';
import { MenuItem, ListItemIcon, Badge } from '@material-ui/core';
import Tour from 'reactour';
import { InfoRounded } from '@material-ui/icons';
import useStore from '../../utils/apiStore';
import { useLocation } from 'react-router-dom';
import gif from '../../assets/transitions.gif';

const steps = [
  {
    selector: '.step-settings',
    content: (
      <div>
        <h2>Cài đặt hướng dẫn</h2>
        Khám phá chi tiết về từng cài đặt
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-four',
    content: (
      <div>
        <h2>Các nút điều khiển</h2>
        Không cần giải thích
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-six',
    content: (
      <div>
        <h2>Chuyển tiếp tổng thể</h2>
        Phản chiếu thay đổi chuyển tiếp đến tất cả các đèn
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-seven',
    content: (
      <div>
        <h2>Tìm khi khởi động</h2>
        Tìm các đèn đã kết nối khi khởi động WiFi Led Studio
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-one',
    content: (
      <div>
        <h2>Thiết bị âm thanh</h2>
        Chọn thiết bị âm thanh đầu vào của bạn tại đây
        <p>
          Lưu ý: Thông tin bổ sung đến
        </p>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-two',
    content: (
      <div>
        <h2>FPS Giao diện người dùng</h2>
        FPS được gửi đến giao diện người dùng để hiển thị biểu đồ LED
        <p>
          Lưu ý: Các thiết bị cấu hình yếu có thể gặp khó khăn với quá nhiều dữ liệu.
          Giữ nó ở mức tối đa, nếu mọi thứ chạy trơn tru.
        </p>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-three',
    content: (
      <div>
        <h2>Độ dài pixel tối đa của giao diện người dùng</h2>
        Các điểm ảnh trên mỗi thiết bị được gửi đến giao diện người dùng để hiển thị PixelGraphs
        <p>
          Lưu ý: Các thiết bị cấp thấp có thể gặp khó khăn với quá nhiều dữ liệu.
        </p>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-five',
    content: (
      <div>
        <h2>Tích hợp Rainbow Music Led </h2>
        Tinh chỉnh cách WiFi Led Studio nên xử lý các đèn của Rainbow Music Led
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-settings-eight',
    content: (
      <div>
        <h2>Chuyển tiếp</h2>
          <p>Tinh chỉnh cách WiFi Led Studio thay đổi từ hiệu ứng này sang hiệu ứng khác</p>
        <div style={{ display: 'flex'}}>
        <img src={gif} />
        </div>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
      maxWidth: 600
    },
  },
];

const TourSettings = ({ cally }) => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const setTour = useStore((state) => state.setTour);
  const invisible = useStore((state) => state.tours.settings);
  const settingsExpanded = useStore((state) => state.settingsExpanded);
  const setSettingsExpanded = useStore((state) => state.setSettingsExpanded);
  const features = useStore((state) => state.features);

  useLayoutEffect(()=>{
    if (isTourOpen && settingsExpanded !== 'all') {
      setSettingsExpanded('all')
    }
  },[isTourOpen])

  return (
    <>
      <MenuItem onClick={(e) => { 
        setIsTourOpen(true); 
        cally(e);
        setTour("settings");
        }}>
        <ListItemIcon>
          <Badge variant="dot" color="primary" invisible={invisible}>
            <InfoRounded />
          </Badge>
        </ListItemIcon>
        Hướng dẫn
      </MenuItem>
      <Tour
        steps={features["rml"] ? steps : steps.filter(s=>s.selector !== '.step-settings-five')}
        accentColor="#800000"
        isOpen={isTourOpen}
        onRequestClose={() => {
          setSettingsExpanded('false')
          setIsTourOpen(false)
        }}
      />
    </>
  );
};

export default TourSettings;
