import { useEffect } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { Card, CardHeader, CardContent, InputLabel, MenuItem, FormControl, Checkbox, Icon, TextField, Select,  Accordion, AccordionDetails, AccordionSummary, Typography } from '@material-ui/core';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import Rml from '../../components/Icons/Rml';
import useStore from '../../utils/apiStore';

const useStyles = makeStyles({
    content: {
        display: 'flex',
        flexDirection: 'column',
    },
    rowContainer: {
        border: '1px solid',
        borderRadius: '4px'
    },
    rowB: {
        display: 'flex',
        flexDirection: 'row'
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        padding: '10px 5px',
        '&:not(:last-child)': {
            borderBottom: '1px solid',
        }
    },
    formControl: {
        width: '100%',
        marginRight: '1rem',
    },
    check: {
        '& .MuiSvgIcon-root': {
            width: '2rem',
            height: '2rem',
        }
    },

});

const RmlCard = ({ className }) => {

    const classes = useStyles();
    const setSystemConfig = useStore(state => state.setSystemConfig);
    const getSystemConfig = useStore((state) => state.getSystemConfig);
    const settings = useStore(state => state.config);

    const toggleSetting = (setting, value) => {
        setSystemConfig({ config: { rml_preferences: { [setting]: { user_enabled: value } } } }).then(() => getSystemConfig());
    }
    const onChangeSetting = (setting, value) => {
        setSystemConfig({ config: { rml_preferences: { [setting]: { setting: value } } } }).then(() => getSystemConfig());
    }
    const onScanOnStart = (setting, value) => {
        setSystemConfig({ config: { [setting]: value } }).then(() => getSystemConfig());
    }

    useEffect(() => {
        getSystemConfig();
    }, [getSystemConfig]);

    return settings.rml_preferences ? (
        <Card style={{ marginBottom: '2rem' }} className={className}>
            <CardHeader title="RML Integration" subheader="Configure RML-Settings" action={
                <Icon
                    style={{
                        margin: '1rem',
                        fontSize: '2.5rem'
                    }}
                >
                    <Rml />
                </Icon>} />
            <CardContent className={classes.content}>
                <FormControl>
                    <InputLabel id="rml-scan-selector">Tìm đèn khi khởi động</InputLabel>
                    <Select
                        labelId="rml-scan-selector"
                        id="rml-scan-select"
                        value={settings.scan_on_startup}
                        onChange={(e) => onScanOnStart("scan_on_startup", e.target.value)}
                    >
                        <MenuItem value={true}>Có</MenuItem>
                        <MenuItem value={false}>Không</MenuItem>
                    </Select>
                </FormControl>
                <Accordion style={{ marginTop: '2rem' }}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="panel1bh-content"
                        id="panel1bh-header"
                    >
                        <Typography className={classes.heading}>Cài đặt đồng bộ đèn Rainbow Music Led</Typography>
                    </AccordionSummary>
                    <AccordionDetails className={classes.content}>
                        <p style={{ margin: '0 0 2rem 0' }}>WiFi Led Studio có thể định cấu hình cài đặt đồng bộ hóa của đèn Rainbow Music Led thành các giá trị được đề xuất.<br /><br />
                            Cảnh báo: <br />
                            Nếu bạn đang sử dụng đèn của mình với các bộ điều khiển khác, những thay đổi đối với các cài đặt này có thể ảnh hưởng đến chức năng của chúng! <br /> <br />
                            WiFi Led Studio sẽ chỉ thay đổi cài đặt bạn chọn bằng cách tích vào ô chọn</p>
                        <div className={classes.rowContainer}>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.rml_preferred_mode.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("rml_preferred_mode", !settings.rml_preferences.rml_preferred_mode.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <FormControl className={classes.formControl}>
                                    <InputLabel id="rml-mode-selector">Chế độ đồng bộ</InputLabel>
                                    <Select
                                        labelId="rml-mode-selector"
                                        id="rml-mode-select"
                                        value={settings.rml_preferences.rml_preferred_mode.setting}
                                        onChange={(e) => onChangeSetting("rml_preferred_mode", e.target.value)}
                                        disabled={!settings.rml_preferences.rml_preferred_mode.user_enabled}
                                    >
                                        <MenuItem value={"unset"}>Không cài</MenuItem>
                                        <MenuItem value={"E131"}>E131</MenuItem>
                                        <MenuItem value={"DDP"}>DDP</MenuItem>
                                        <MenuItem value={"UDP"}>UDP</MenuItem>
                                    </Select>
                                </FormControl>
                            </div>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.realtime_gamma_enabled.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("realtime_gamma_enabled", !settings.rml_preferences.realtime_gamma_enabled.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <FormControl className={classes.formControl}>
                                    <InputLabel id="rml-gamma">Gamma thời gian thực</InputLabel>
                                    <Select
                                        labelId="rml-gamma"
                                        id="rml-gamma-select"
                                        value={settings.rml_preferences.realtime_gamma_enabled.setting}
                                        onChange={(e) => onChangeSetting("realtime_gamma_enabled", e.target.value)}
                                        disabled={!settings.rml_preferences.realtime_gamma_enabled.user_enabled}
                                    >
                                        <MenuItem value={true}>Bật</MenuItem>
                                        <MenuItem value={false}>Tắt</MenuItem>
                                    </Select>
                                </FormControl>
                            </div>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.force_max_brightness.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("force_max_brightness", !settings.rml_preferences.force_max_brightness.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <FormControl className={classes.formControl}>
                                    <InputLabel id="rml-brightness">Luôn sáng tối đa</InputLabel>
                                    <Select
                                        labelId="rml-brightness"
                                        id="rml-brightness-select"
                                        value={settings.rml_preferences.force_max_brightness.setting}
                                        onChange={(e) => onChangeSetting("force_max_brightness", e.target.value)}
                                        disabled={!settings.rml_preferences.force_max_brightness.user_enabled}
                                    >
                                        <MenuItem value={true}>Bật</MenuItem>
                                        <MenuItem value={false}>Tắt</MenuItem>
                                    </Select>
                                </FormControl>
                            </div>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.realtime_dmx_mode.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("realtime_dmx_mode", !settings.rml_preferences.realtime_dmx_mode.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <FormControl  className={classes.formControl}>
                                    <InputLabel id="rml-dmx">Chế độ DMX</InputLabel>
                                    <Select
                                        labelId="rml-dmx"
                                        id="rml-dmx-select"
                                        value={settings.rml_preferences.realtime_dmx_mode.setting}
                                        onChange={(e) => onChangeSetting("realtime_dmx_mode", e.target.value)}
                                        disabled={!settings.rml_preferences.realtime_dmx_mode.user_enabled}
                                    >
                                        <MenuItem value={"MultiRGB"}>Tắt</MenuItem>
                                        <MenuItem value={"MultiRGB"}>RGB đơn</MenuItem>
                                        <MenuItem value={"MultiRGB"}>DRGB đơn</MenuItem>
                                        <MenuItem value={"MultiRGB"}>Đa RGB</MenuItem>
                                        <MenuItem value={"MultiRGB"}>Mờ + đa RGB</MenuItem>
                                        <MenuItem value={"MultiRGB"}>Đa RGBW</MenuItem>
                                    </Select>
                                </FormControl>
                            </div>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.start_universe_setting.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("start_universe_setting", !settings.rml_preferences.start_universe_setting.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <TextField
                                    type="number"
                                    label="Universe đầu tiên"
                                    id="rml-universe-select"
                                    value={settings.rml_preferences.start_universe_setting.setting}
                                    onChange={(e) => onChangeSetting("start_universe_setting", e.target.value)}
                                    disabled={!settings.rml_preferences.start_universe_setting.user_enabled} 
                                    className={classes.formControl} />

                            </div>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.dmx_address_start.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("dmx_address_start", !settings.rml_preferences.dmx_address_start.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <TextField
                                    type="number"
                                    label="Địa chỉ DMX đầu tiên"
                                    id="rml-dmx-start-select"
                                    value={settings.rml_preferences.dmx_address_start.setting}
                                    onChange={(e) => onChangeSetting("dmx_address_start", e.target.value)}
                                    disabled={!settings.rml_preferences.dmx_address_start.user_enabled}
                                    className={classes.formControl}
                                />

                            </div>
                            <div className={classes.row}>

                                <Checkbox
                                    checked={settings.rml_preferences.inactivity_timeout.user_enabled}
                                    className={classes.check}
                                    onChange={() => toggleSetting("inactivity_timeout", !settings.rml_preferences.inactivity_timeout.user_enabled)}
                                    inputProps={{ 'aria-label': 'primary checkbox' }}
                                />
                                <TextField
                                    type="number"
                                    label="Thời gian chờ không hoạt động"
                                    id="rml-inactivity-select"
                                    value={settings.rml_preferences.inactivity_timeout.setting}
                                    onChange={(e) => onChangeSetting("inactivity_timeout", e.target.value)}
                                    disabled={!settings.rml_preferences.inactivity_timeout.user_enabled}
                                    className={classes.formControl}
                                />
                            </div>
                        </div>
                    </AccordionDetails>
                </Accordion >
            </CardContent >
        </Card >
    ) : (<></>);
};

export default RmlCard;
