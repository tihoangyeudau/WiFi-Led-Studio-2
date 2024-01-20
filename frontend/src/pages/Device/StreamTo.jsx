import * as React from 'react';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import WifiIcon from '@mui/icons-material/Wifi';
import BluetoothIcon from '@mui/icons-material/Bluetooth';
import { makeStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import CardHeader from '@material-ui/core/CardHeader';
import FormControl from '@material-ui/core/FormControl';
import Switch from '@material-ui/core/Switch';
import MenuItem from '@material-ui/core/MenuItem';
import InputLabel from '@material-ui/core/InputLabel';
import { useEffect, useRef, useState } from 'react'
import useStore from '../../utils/apiStore';
import { deepEqual } from '../../utils/helpers'
import BladeFrame from '../../components/SchemaForm/components/BladeFrame';
import BladeIcon from '../../components/Icons/BladeIcon/BladeIcon';
import { Button, CardActions, Chip, OutlinedInput, Select } from '@material-ui/core';
import { Box } from '@mui/system';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const useStyles = makeStyles((theme) => ({
  content: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    padding: theme.spacing(2),
    paddingBottom: 0,
  },
  card: { width: '100%', maxWidth: '540px', marginBottom: '1rem' },
}));

const StreamToCard = ({ virtual, virtuals, style }) => {
  const classes = useStyles();
  const cref = useRef(null);
  const streamingToDevices = useStore((state) => state.streamingToDevices);
  const setStreamingToDevices = useStore((state) => state.setStreamingToDevices);

  const [streamingTo, setStreamingTo] = React.useState(streamingToDevices.indexOf(virtual.id) === -1 ? [virtual.id] : streamingToDevices);
  const streaming = useStore((state) => state.streaming);
  const setStreaming = useStore((state) => state.setStreaming);
  const getVirtuals = useStore((state) => state.getVirtuals);

  const copyTo = useStore((state) => state.copyTo);

  const handleToggle = (value) => {
    const currentIndex = streamingTo.indexOf(value);
    const newStreamingDevices = [...streamingTo];
    if (currentIndex === -1) {
      newStreamingDevices.push(value);
    } else {
      newStreamingDevices.splice(currentIndex, 1);
    }
    setStreamingTo(newStreamingDevices);
    setStreamingToDevices(newStreamingDevices)
  };

  const handleCopy = () =>
    copyTo(virtual.id, streamingTo).then(() => getVirtuals())

  useEffect(() => {
    if (streaming) {
      if (!deepEqual(cref.current, virtuals[virtual.id]?.effect)) {
        if (cref.current !== null) handleCopy()
        cref.current = virtuals[virtual.id]?.effect
      }
    }
  }, [virtuals[virtual.id]?.effect]);

  return (
    <Card variant="outlined" className={`${classes.card} step-device-two`} style={style}>
      <CardHeader title="Đồng bộ" subheader="Đồng bộ hiệu ứng hiện tại sang các đèn khác" style={{ paddingBottom: 11 }} />
      <CardContent className={classes.content}>
        <FormControl style={{ margin: 10, width: "100%" }}>
          <InputLabel id="demo-multiple-chip-label" style={{ margin: '-7px 0 0 14px' }}>Chọn (các) đèn để đồng bộ</InputLabel>
          <Select
            labelId="demo-multiple-chip-label"
            id="demo-multiple-chip"
            multiple
            value={streamingTo}
            onChange={(e, b) => handleToggle(b.props.value)}
            input={<OutlinedInput id="select-multiple-chip" label="Chọn (các) đèn để đồng bộ" />}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {selected.map((value) => (
                  <Chip key={value} label={value} />
                ))}
              </Box>
            )}
            MenuProps={MenuProps}
          >
            {Object.keys(virtuals).map((name) => (
              <MenuItem
                key={name}
                value={name}
              // style={getStyles(name, personName, theme)}
              >
                {name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <Button
            style={{ marginBottom: '10px', border: '1px solid #61666c', fontSize: '9px' }}
            size="medium"
            onClick={() => handleCopy()}
          >
            Đồng bộ<br />1 lần
          </Button>
          <Button
            style={{ marginBottom: '10px', border: '1px solid #61666c', fontSize: '9px' }}
            size="medium"
            onClick={() => setStreaming(!streaming)}
            color={streaming ? 'primary' : 'inherit'}
          >
            Luôn<br />đồng bộ
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default StreamToCard;
