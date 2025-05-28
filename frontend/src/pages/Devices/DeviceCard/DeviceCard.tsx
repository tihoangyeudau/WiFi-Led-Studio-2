import { useState, useEffect } from 'react';
import clsx from 'clsx';
import { useTheme } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import Button from '@material-ui/core/Button';
import SettingsIcon from '@material-ui/icons/Settings';
import VisibilityIcon from '@material-ui/icons/Visibility';
import TuneIcon from '@material-ui/icons/Tune';
import { NavLink } from 'react-router-dom';
import Collapse from '@material-ui/core/Collapse';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import {
  Clear,
  Delete,
  Pause,
  PlayArrow,
  SyncProblem,
} from '@material-ui/icons';
import Popover from '../../../components/Popover/Popover';
import EditVirtuals from '../EditVirtuals/EditVirtuals';
import PixelGraph from '../../../components/PixelGraph';
import BladeIcon from '../../../components/Icons/BladeIcon/BladeIcon';
import useStyle from './DeviceCard.styles';
import { DeviceCardDefaults, DeviceCardProps } from './DeviceCard.interface';

/**
 * Pixelgraphs will not connect via Websocket in Storybook
 *
 */
const DeviceCard = ({
  deviceName,
  online,
  virtId,
  index,
  handleDeleteDevice,
  handleEditVirtual,
  handleClearEffect,
  handlePlayPause,
  linkTo,
  additionalStyle,
  iconName,
  graphsActive,
  colorIndicator,
  effectName,
  isPlaying,
  isStreaming,
  previewOnly,
  isEffectSet,
  transitionTime,
  isDevice,
  activateDevice,
}: DeviceCardProps) => {
  const classes = useStyle();
  const theme = useTheme();
  // eslint-disable-next-line
  const [fade, _setFade] = useState(false);
  const [isActive, setIsActive] = useState(isEffectSet || isStreaming);
  const [lastEventTime, setLastEventTime] = useState(0);

  const [expanded, setExpanded] = useState(false);
  const color = 'inherit';

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  // Lắng nghe sự kiện ledStateChanged để cập nhật UI ngay lập tức
  useEffect(() => {
    const handleLedStateChanged = (e: CustomEvent) => {
      // Cập nhật trạng thái active dựa trên sự kiện
      if (e.detail && typeof e.detail.is_active !== 'undefined') {
        const { is_active, device_id } = e.detail;

        // Chỉ cập nhật nếu sự kiện là cho tất cả thiết bị hoặc cho thiết bị cụ thể này
        if (!device_id || (isDevice === device_id)) {
          setIsActive(is_active);
          setLastEventTime(Date.now()); // Cập nhật thời gian sự kiện gần nhất

          // Ghi log để debug
          console.log(`DeviceCard.tsx: Cập nhật isActive=${is_active} cho thiết bị ${virtId}, device_id=${device_id}`);
        }
      }
    };

    // Thêm type assertion để TypeScript hiểu rằng đây là một CustomEvent
    document.addEventListener('ledStateChanged', handleLedStateChanged as EventListener);
    return () => {
      document.removeEventListener('ledStateChanged', handleLedStateChanged as EventListener);
    };
  }, [isDevice, virtId]);

  // Cập nhật trạng thái dựa trên props, nhưng chỉ khi không có sự kiện ledStateChanged gần đây
  useEffect(() => {
    // Chỉ cập nhật từ props nếu không có sự kiện ledStateChanged trong 500ms gần đây
    const now = Date.now();
    if (now - lastEventTime > 500) {
      setIsActive(isEffectSet || isStreaming);
      console.log(`DeviceCard.tsx: Cập nhật isActive từ props: isEffectSet=${isEffectSet}, isStreaming=${isStreaming}`);
    }
  }, [isEffectSet, isStreaming, lastEventTime]);

  return (
    <NavLink
      to={linkTo}
      className={`${classes.virtualCardPortraitW} ${
        isEffectSet ? 'active' : ''
      } ${online ? 'trực tuyến' : 'ngoại tuyến'}`}
      style={{ ...additionalStyle, width: '100%' }}
    >
      <Card className={classes.virtualCardPortrait}>
        <div className={classes.virtualCardContainer}>
          <div className={`${classes.virtualIconWrapper}`}>
            <BladeIcon
              colorIndicator={false}
              name={iconName}
              className={`${classes.virtualIcon} ${
                !graphsActive ? 'graphs' : ''
              } ${expanded ? 'extended' : ''}`}
              style={{ zIndex: 3, opacity: online ? 1 : 0.3 }}
              card
            />
          </div>

          <div style={{ padding: '0 0.5rem' }}>
            <Typography
              variant="h6"
              style={{
                lineHeight: 1,
                color: colorIndicator ? theme.palette.primary.light : 'inherit',
                opacity: online ? 1 : 0.3,
              }}
            >
              {deviceName}
            </Typography>
            {!online ? (
              <Typography
                variant="body1"
                color="textSecondary"
                style={{
                  height: 25,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <Typography
                  variant="body1"
                  component="span"
                  color="textSecondary"
                  style={{
                    height: 25,
                    opacity: online ? 1 : 0.3,
                  }}
                >
                  ngoại tuyến
                </Typography>
                <Button
                  size="small"
                  onClick={(e) => {
                    e.preventDefault();
                    if (isDevice) {
                      activateDevice(isDevice);
                    }
                  }}
                  style={{
                    color: 'inherit',
                    marginLeft: '1rem',
                    marginTop: '0rem',
                    minWidth: 'unset',
                    zIndex: expanded ? 1 : 3,
                  }}
                >
                  <SyncProblem />
                </Button>
              </Typography>
            ) : effectName ? (
              <Typography
                variant="body1"
                color="textSecondary"
                style={{ height: 25, display: 'flex', alignItems: 'center' }}
              >
                Hiệu ứng: {effectName}
                <Button
                  size="small"
                  onClick={(e) => {
                    e.preventDefault();
                    handlePlayPause();
                  }}
                  style={{
                    color: '#999',
                    minWidth: 'unset',
                    zIndex: expanded ? 1 : 3,
                  }}
                >
                  {isPlaying ? <Pause /> : <PlayArrow />}
                </Button>
                <Button
                  size="small"
                  onClick={(e) => {
                    e.preventDefault();
                    handleClearEffect(virtId);
                  }}
                  style={{
                    color: '#999',
                    minWidth: 'unset',
                    zIndex: expanded ? 1 : 3,
                  }}
                >
                  <Clear />
                </Button>
              </Typography>
            ) : !isActive ? (
              // Nếu isActive là false (từ sự kiện ledStateChanged), luôn hiển thị "tắt"
              <Typography
                variant="body1"
                style={{ color: theme.palette.text.disabled, height: 25 }}
              >
                tắt
              </Typography>
            ) : isStreaming ? (
              // Nếu isActive là true và isStreaming cũng true, hiển thị "Đang truyền..."
              <Typography
                variant="body1"
                color="textSecondary"
                style={{ height: 25 }}
              >
                Đang truyền...
              </Typography>
            ) : (
              // Trường hợp còn lại
              <Typography
                variant="body1"
                style={{ color: theme.palette.text.disabled, height: 25 }}
              >
                tắt
              </Typography>
            )}
          </div>

          <div>
            {previewOnly && (
              <Button variant="text" disabled size="small">
                <VisibilityIcon />
              </Button>
            )}
          </div>

          <IconButton
            className={clsx(classes.expand, {
              [classes.expandOpen]: expanded,
            })}
            onClick={(e) => {
              e.preventDefault();
              handleExpandClick();
            }}
            aria-expanded={expanded}
            aria-label="hiển thị thêm"
            style={{ zIndex: 3, color: '#999' }}
          >
            <ExpandMoreIcon className={`step-devices-two-${index}`} />
          </IconButton>
        </div>
        <div
          className={clsx(classes.pixelbar, {
            [classes.pixelbarOut]: fade,
          })}
          style={{ transitionDuration: `${transitionTime}s` }}
        >
          <PixelGraph
            intGraphs={graphsActive}
            active={isActive}
            virtId={virtId}
            className="step-devices-seven"
          />
        </div>
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            right: 0,
            zIndex: 2,
          }}
        >
          <Collapse
            in={expanded}
            timeout="auto"
            unmountOnExit
            className={classes.buttonBarMobile}
          >
            {/* eslint-disable-next-line */}
            <div
              className={`${classes.buttonBarMobileWrapper} ${
                !graphsActive ? 'graphs' : ''
              } ${expanded ? 'extended' : ''}`}
              onClick={(e) => e.preventDefault()}
            >
              <div />
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-end',
                  justifyContent: 'center',
                }}
              >
                <Popover
                  variant="text"
                  startIcon={<Delete />}
                  label="xoá"
                  color={color}
                  onConfirm={() => handleDeleteDevice(virtId)}
                  className={`step-devices-three-${index}`}
                  style={{ width: '100%' }}
                />

                {isDevice ? (
                  null
                ) : (
                  <EditVirtuals
                    label="Sửa đèn ảo"
                    variant="text"
                    color={color}
                    virtId={virtId}
                    icon={undefined}
                    className="step-devices-six"
                    startIcon={<TuneIcon />}
                    type={undefined}
                    innerKey={undefined}
                  />
                )}
                <Button
                  variant="text"
                  size="small"
                  startIcon={<SettingsIcon />}
                  color={color}
                  className={`step-devices-five-${index}`}
                  onClick={(e) => {
                    e.preventDefault();
                    handleEditVirtual(virtId);
                  }}
                >
                  Cài đặt
                </Button>
              </div>
            </div>
          </Collapse>
        </div>
      </Card>
    </NavLink>
  );
};

DeviceCard.defaultProps = DeviceCardDefaults;

export default DeviceCard;
