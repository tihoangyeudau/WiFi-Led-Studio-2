import { useState } from 'react';
import { Button } from '@material-ui/core';
import Tour from 'reactour';
import useStore from '../../utils/apiStore';

const steps = [
  {
    selector: '.step-zero',
    content: (
      <div>
        <h2>Hướng dẫn</h2>
        Chào mừng đến với WiFi Led Studio! Vui lòng theo dõi quá trình hướng dẫn này và chúng tôi sẽ chỉ cho bạn
         cách sử dụng phần mềm nhé 😊
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-one',
    content: (
      <div>
        <h2>Dẫn đường</h2>
        Đi đến các trang khác nhau từ đây
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-two',
    content: (
      <div>
        <h2>Menu</h2>
        Các hành động và cài đặt của WiFi Led Studio có thể được tìm thấy tại đây
        <ul style={{ paddingLeft: '1rem' }}>
          <li>👨‍🏫 Bạn có thể truy cập một hướng dẫn cho các trang khác trong menu này</li>
          <li>
            👀 &apos;Bật biểu đồ&apos; để xem trước các đèn LED của thiết bị.
             Hãy tắt nó đi nếu trình duyệt của bạn gặp khó khăn với quá nhiều led!
          </li>
        </ul>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-three',
    content: (
      <div>
        <h2>Truy cập đèn nhanh</h2>
        Trực tiếp chuyển đến một đèn
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
  {
    selector: '.step-four',
    content: (
      <div>
        <h2>Nút tròn lớn</h2>
        Đây là nơi mà tất cả bắt đầu!
        <ul style={{ paddingLeft: '1rem' }}>
          <li>Thêm thiết bị: Thêm dải đèn LED đã kết nối WiFi</li>
          <li>
            Thêm đèn ảo: Chia hoặc hợp nhất các đèn của bạn thành một đèn ảo
          </li>
          <li>Thêm cảnh: Lưu các hiệu ứng hoạt động của tất cả các đèn</li>
          <li>
            Thêm tích hợp: Kết nối WiFi Led Studio với phần mềm khác (sắp có ...)
          </li>
        </ul>
        Bây giờ bạn nên kết thúc hướng dẫn này và thêm đèn đầu tiên của bạn vào
         WiFi Led Studio nhé 🎉
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
];

const TourHome = () => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const setTour = useStore((state) => state.setTour);
  return (
    <>
      <Button
        variant="outlined"
        className="step-zero"
        onClick={() => {
          setTour('home');
          setIsTourOpen(true);
        }}
      >
        Hướng dẫn
      </Button>
      <Tour
        steps={steps}
        accentColor="#800000"
        isOpen={isTourOpen}
        onRequestClose={() => setIsTourOpen(false)}
      />
    </>
  );
};

export default TourHome;
