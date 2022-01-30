import { useState } from 'react';
import { MenuItem, ListItemIcon, Badge } from '@material-ui/core';
import Tour from 'reactour';
import { InfoRounded } from '@material-ui/icons';
import useStore from '../../utils/apiStore';

const steps = [
  {
    selector: '.step-scenes-one',
    content: (
      <div>
        <h2>Cảnh</h2>
        Bạn có thể lưu trạng thái hiện tại của WiFi Led Studio dưới dạng một cảnh,
        trong khi đặt tên cho nó và tùy chọn một hình ảnh hoặc một biểu tượng.
        <p>
        Lưu ý: Điều này bao gồm tất cả các hiệu ứng đang hoạt động cho tất cả các thiết bị và cài đặt hiệu ứng của chúng.
        </p>
      </div>
    ),
    style: {
      backgroundColor: '#303030',
    },
  },
];

const TourScenes = ({ cally }) => {
  const [isTourOpen, setIsTourOpen] = useState(false);
  const setTour = useStore((state) => state.setTour);
  const invisible = useStore((state) => state.tours.devices);

  return (
    <>
      <MenuItem onClick={(e) => { 
        setIsTourOpen(true); 
        cally(e);
        setTour("scenes");
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

export default TourScenes;
