import { useState, forwardRef } from 'react';
import { Button, Dialog, AppBar, Toolbar, Typography, Slide, Divider, Icon, Grid, CircularProgress } from '@material-ui/core';
import { BugReport, NavigateBefore } from '@material-ui/icons';
import { useTroubleshootStyles } from './Troubleshoot.styles';
import useStore from '../../utils/apiStore';
import Rml from '../../components/Icons/Rml';
import Moment from 'react-moment';
import moment from 'moment';

const Transition = forwardRef(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});

export default function TroubleshootButton({ virtual }) {
  const classes = useTroubleshootStyles();
  const devices = useStore((state) => state.devices);
  const getPing = useStore((state) => state.getPing);
  const [open, setOpen] = useState(false);
  const [rmlData, setRmlData] = useState({});
  const [pingData, setPingData] = useState({});
  const [loading, setLoading] = useState(false);

  const ping = async () => {
    if (devices[virtual.id]) {
      if (!loading) { setLoading(true) }
      const res = await fetch(`http://${devices[virtual.id]["config"]["ip_address"]}/json/info`)
      const resp = await res.json()
      setRmlData(resp)
      const ping = getPing(virtual.id)
      const resPing = await ping
      setPingData(resPing)
    }
  }

  const Row = ({ name, value }) => {
    return <div className={classes.row}>
      <Typography className={classes.title}>{name}</Typography>
      {typeof value === 'object' ? value : <Typography>{value}</Typography>}
    </div>
  }

  return virtual && virtual.config && devices[virtual.id] && devices[virtual.id].type === 'rml' ? (
    <>
      <Button
        variant={'outlined'}
        color={'default'}
        onClick={() => setOpen(true)}
        style={{ marginRight: '.5rem' }}
      >
        <BugReport />
      </Button>
      <Dialog fullScreen open={open} onClose={() => setOpen(false)} TransitionComponent={Transition}>
        <AppBar className={classes.appBar}>
          <Toolbar>
            <Button
              color="primary"
              variant="contained"
              startIcon={<NavigateBefore />}
              onClick={() => setOpen(false)}
              style={{ marginRight: '1rem' }}
            >
              quay lại
            </Button>
            <Typography variant="h6" className={classes.title}>
              {virtual.config.name}{' '}
            </Typography>
          </Toolbar>
        </AppBar>
        <div>
          <div className={classes.segmentTitle}>
            <Typography variant="caption">Khắc phục sự cố</Typography>
          </div>
          {rmlData.name
            ? <Grid container spacing={4} style={{ width: 'calc(max(38.5vw, 480px))', paddingLeft: '0.5rem', margin: '0 auto' }}>
              <Grid item xs={12} lg={6}>
                <Divider style={{ marginBottom: '0.25rem', }} />
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', fontSize: '1.5rem', }}>
                  <Icon style={{ marginRight: '0.7rem', }}> <Rml /></Icon> {rmlData.name}</div>
                <Divider style={{ margin: '0.25rem 0 1rem 0' }} />
                <Row name={'AVERAGE PING'} value={pingData.max_ping ? `${pingData.max_ping.toFixed(2)} ms` : <CircularProgress size={12} />} />
                <Row name={'AVERAGE PING'} value={pingData.avg_ping ? `${pingData.avg_ping.toFixed(2)} ms` : <CircularProgress size={12} />} />
                <Row name={'MINIMUM PING'} value={pingData.min_ping ? `${pingData.min_ping.toFixed(2)} ms` : <CircularProgress size={12} />} />
                <Row name={'PACKETS LOST'} value={`${pingData.packetlosspercent ? pingData.packetlosspercent.toFixed(2) : 0} %`} />
                <Divider style={{ margin: '1rem 0' }} />
                <Row name={'WiFi Signal strength'} value={`${rmlData.wifi?.signal} %`} />
                <Row name={'WiFi Channel'} value={rmlData.wifi?.channel} />
                <Row name={'MAC'} value={rmlData.mac} />
                <Row name={'Frames Per Second'} value={`${rmlData.leds?.fps} fps`} />
              </Grid>
              <Grid item xs={12} lg={6}>
                <Divider style={{ margin: ' 0 0 0.5rem 0' }} />
                <Row name={'Version'} value={rmlData.ver} />
                <Row name={'Chip'} value={rmlData.arch} />
                <Row name={'LED Count'} value={rmlData.leds?.count} />
                <Row name={'RGBW'} value={JSON.stringify(rmlData.leds?.rgbw)} />
                <Row name={'Estimated Power'} value={`${rmlData.leds?.pwr?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')} mA`} />
                <Row name={'Max power'} value={`${rmlData.leds?.maxpwr?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')} mA`} />
                <Row name={'Live Mode'} value={JSON.stringify(rmlData.live)} />
                <Row name={'Live Mode Source'} value={rmlData.lip} />
                <Row name={'Live Mode Protocol'} value={rmlData.lm} />
                <Row name={'UDP Port'} value={rmlData.udpport} />
                <Row name={'Uptime'} value={<Moment interval={1000} format="hh:mm:ss" durationFromNow>{moment().add(rmlData.uptime * -1, 's')}</Moment>} />
              </Grid>
            </Grid>
            : <div style={{ textAlign: 'center', margin: 10 }}>
              <Button variant={'outlined'} disabled={loading} onClick={ping}>Quét </Button>
            </div>}
        </div>
      </Dialog>
    </>
  ) : (<></>);
}