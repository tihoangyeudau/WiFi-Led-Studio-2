import { Card, CardHeader } from '@material-ui/core';
import { Info } from '@material-ui/icons';
import PropTypes from 'prop-types';

interface NoYetProps {
  type?: string;
}

const NoYet: React.FC<NoYetProps> = ({ type }): JSX.Element => (
  <Card>
    <CardHeader
      avatar={<Info />}
      title={`Không có ${type} nào`}
      subheader={`Bạn có thể thêm ${type} đầu tiên bằng cách bấm vào nút Tròn cộng`}
    />
  </Card>
);

NoYet.propTypes = {
  type: PropTypes.string,
};

NoYet.defaultProps = {
  type: 'Thing',
};

export default NoYet;
