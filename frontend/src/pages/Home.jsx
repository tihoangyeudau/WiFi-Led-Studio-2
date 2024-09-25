import { useState } from "react";
import {
  Button,
  Box,
  Typography,
  Card,
  CardHeader,
  CardContent,
  CardActions,
  CircularProgress,
  Badge,
} from '@material-ui/core';
import TourHome from '../components/Tours/TourHome';
import useStore from '../utils/apiStore';
import logoMain from "../assets/logomain.png";
import { deleteFrontendConfig } from "../utils/helpers";
import ButtonBar from "../components/ButtonBar";
// import useAddToHomescreenPrompt from "../utils/useAddToHomeScreenPromt";

const sleep = ms => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export default function Home(props) {
  const scanForDevices = useStore((state) => state.scanForDevices);
  const getDevices = useStore((state) => state.getDevices);
  const getVirtuals = useStore((state) => state.getVirtuals);
  const [scanning, setScanning] = useState(false)
  const invisible = useStore((state) => state.tours.home);
  // const [promptable, promptToInstall, isInstalled] = useAddToHomescreenPrompt();
  // console.log(promptable, promptToInstall, isInstalled)
  const handleScan = () => {
    setScanning(true)
    scanForDevices().then(async () => {
      for (let sec = 1; sec <= 30; sec++) {
        await sleep(1000).then(() => {
          getDevices();
          getVirtuals();
          setScanning(sec)
        });
      }
    }).then(() => {
      setScanning(false)
    })
  }
  return (
    <>
      <div className="Content">
        <div style={{ position: 'relative' }} >
          <img src={logoMain} className="App-logo" alt="logo-main" />
        </div>
      </div>
      <Card
        variant="outlined"
        style={{
          maxWidth: '400px',
          margin: '0.5rem auto 2rem auto',
        }}
      >
        <CardHeader style={{ textAlign: 'center' }} title="WIFI LED STUDIO" />
        <CardContent style={{ textAlign: 'center' }}>
          RAINBOW MUSIC LED © 2024
          <ul style={{ listStyleType: 'none', padding: 0, textAlign: 'left' }}>
            <li>Website chính thức: <a href="https://rainbowmusicled.com" target="_blank" rel="noopener noreferrer" style={{ color: 'white' }}>https://rainbowmusicled.com</a></li>
            <li>Fanpage: <a href="https://facebook.com/rainbowmusicled/" target="_blank" rel="noopener noreferrer" style={{ color: 'white' }}>https://facebook.com/rainbowmusicled/</a></li>
            <li>Zalo/SĐT: <a href="tel:0981373223" style={{ color: 'white' }}>0981373223</a></li>
          </ul>
        </CardContent>
        <CardActions>
          <Badge variant="dot" color="primary" invisible={invisible}>
            <TourHome className={'step-one'} />
          </Badge>
          <Button onClick={() => handleScan()} variant="outlined">
            {scanning ? <><CircularProgress
              variant="determinate"
              value={(scanning / 30) * 100}
              size={24}
            />
              <Box
                top={0}
                left={0}
                bottom={0}
                right={0}
                position="absolute"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Typography variant="caption" style={{ fontSize: 10 }} component="div" color="textSecondary">{`${Math.round(
                  (scanning / 30) * 100,
                )}%`}</Typography>
              </Box>
            </> : 'Tìm kiếm đèn'}
          </Button>
          <Button variant="outlined" onClick={()=>{
            deleteFrontendConfig()
            }}>
            Xoá dữ liệu
          </Button>
        </CardActions>
      </Card>
      <ButtonBar />
      {/* {promptable && !isInstalled ? (
        <ButtonElement onClick={promptToInstall}>INSTALL APP</ButtonElement>
      ) : null} */}
    </>
  );
}
