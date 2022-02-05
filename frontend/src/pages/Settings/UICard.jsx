import { useEffect, useState } from 'react';
import { Input } from '@material-ui/core';
import useStore from '../../utils/apiStore';
import { useLongPress } from 'use-long-press';
import useSliderStyles from '../../components/SchemaForm/components/Number/BladeSlider.styles';
import { useStyles, SettingsSlider, SettingsSwitch } from './SettingsComponents'

const UICard = () => {
    const classes = useStyles();
    const sliderClasses = useSliderStyles();

    const config = useStore((state) => state.config);
    const getSystemConfig = useStore((state) => state.getSystemConfig);
    const setSystemConfig = useStore((state) => state.setSystemConfig);
    const viewMode = useStore((state) => state.viewMode);
    const setViewMode = useStore((state) => state.setViewMode);
    const graphs = useStore((state) => state.graphs);
    const toggleGraphs = useStore((state) => state.toggleGraphs);
    const setFeatures = useStore((state) => state.setFeatures);
    const showFeatures = useStore((state) => state.showFeatures);
    const setShowFeatures = useStore((state) => state.setShowFeatures);
    const features = useStore((state) => state.features);

    const [fps, setFps] = useState(30)
    const [pixelLength, setPixelLength] = useState(50)
    const [active, setActive] = useState(false);

    const longPress = useLongPress((e) => viewMode === 'expert' &&  setFeatures('dev', true), {
        treshhold: 1000,
        captureEvent: true,
    });    

    const setSystemSetting = (setting, value) => {
        setSystemConfig({ config: { [setting]: value } }).then(() => getSystemConfig());
    }

    useEffect(() => {
        if (typeof config.visualisation_fps === 'number') {
            setFps(config.visualisation_fps)
        }
        if (typeof config.visualisation_maxlen === 'number') {
            setPixelLength(config.visualisation_maxlen)
        }
    }, [config]);

    useEffect(() => {
        getSystemConfig()
    }, []);

    return (
        <div style={{ width: '100%' }}>
            {config.visualisation_fps && (<>
                <div className={`${classes.settingsRow} slider step-settings-two`}>
                    <label>FPS giao diện</label>
                    <div style={{ flexGrow: 1 }}>
                        <SettingsSlider
                            value={fps}
                            // marks={marks}
                            // marks
                            // color=""
                            step={1}
                            // valueLabelDisplay="auto"
                            min={1}
                            max={60}
                            size="medium"
                            onChangeCommitted={(e, val) => setSystemSetting("visualisation_fps", val)}
                            onChange={(e, val) => {
                                setFps(val);
                            }}
                        />
                    </div>
                    <Input
                        disableUnderline
                        className={sliderClasses.input}
                        style={{ width: 50 }}
                        value={fps}
                        margin="dense"
                        onFocus={() => setActive(true)}
                        onChange={(e, val) => {
                            setFps(val);
                        }}
                        onBlur={(e, val) => { setSystemSetting("visualisation_fps", val) }}
                        inputProps={{
                            min: 1,
                            max: 60,
                            type: 'number',
                            'aria-labelledby': 'input-slider',
                        }}
                    />
                </div>

                <div className={`${classes.settingsRow} slider step-settings-three `}>
                    <label>Điểm ảnh giao diện</label>
                    <div style={{ flexGrow: 1 }}>
                        <SettingsSlider
                            value={pixelLength}
                            // marks={marksPixelLength}
                            step={1}
                            valueLabelDisplay="auto"
                            min={1}
                            max={300}
                            onChangeCommitted={(e, val) => setSystemSetting("visualisation_maxlen", val)}
                            onChange={(e, val) => {
                                setPixelLength(val);
                            }}
                        />
                    </div>
                    <Input
                        disableUnderline
                        className={sliderClasses.input}
                        value={pixelLength}
                        style={{ width: 50 }}
                        margin="dense"
                        onChange={(e, val) => {
                            setPixelLength(val);
                        }}
                        onBlur={(e, val) => setSystemSetting("visualisation_maxlen", val)}
                        inputProps={{
                            min: 1,
                            max: 300,
                            type: 'number',
                            'aria-labelledby': 'input-slider',
                        }}
                    />
                </div>

            </>)}
            <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Hiển thị biểu đồ (ngốn CPU)</label>
                <SettingsSwitch checked={graphs} onChange={(e) => toggleGraphs()} />
            </div>
            <div className={`${classes.settingsRow} step-settings-x `}>
                <label {...longPress}>Chế độ nâng cao</label>
                <SettingsSwitch checked={viewMode !== 'user'} onChange={(e) => viewMode === 'user' ? setViewMode("expert") : setViewMode("user")} />
            </div>
            {showFeatures['cloud'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Đám mây</label>
                <SettingsSwitch checked={features['cloud']} onChange={(e) => setFeatures('cloud', !features['cloud'])} />
            </div>}
            {showFeatures['rml'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Tích hợp Rainbow Music Led</label>
                <SettingsSwitch checked={features['rml']} onChange={(e) => setFeatures('rml', !features['rml'])} />
            </div>}
            {showFeatures['integrations'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Tích hợp</label>
                <SettingsSwitch checked={features['integrations']} onChange={(e) => setFeatures('integrations', !features['integrations'])} />
            </div>}            
            {showFeatures['webaudio'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Âm thanh Web</label>
                <SettingsSwitch checked={features['webaudio']} onChange={(e) => setFeatures('webaudio', !features['webaudio'])} />
            </div>}            
            {showFeatures['go'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Nền tảng mới (Go)</label>
                <SettingsSwitch checked={features['go']} onChange={(e) => setFeatures('go', !features['go'])} />
            </div>}            
            {viewMode !== 'user' && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Sao chép sang</label>
                <SettingsSwitch checked={features['streamto']} onChange={(e) => setFeatures('streamto', !features['streamto'])} />
            </div>}
            {showFeatures['effectfilter'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>lọc hiệu ứng</label>
                <SettingsSwitch checked={features['effectfilter']} onChange={(e) => setFeatures('effectfilter', !features['effectfilter'])} />
            </div>}
            {viewMode !== 'user' && <div className={`${classes.settingsRow} step-settings-eight `}>
                <label>Chuyển tiếp</label>
                <SettingsSwitch checked={features['transitions']} onChange={(e) => setFeatures('transitions', !features['transitions'])} />
            </div>}
            {viewMode !== 'user' && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Tần số</label>
                <SettingsSwitch checked={features['frequencies']} onChange={(e) => setFeatures('frequencies', !features['frequencies'])} />
            </div>}
            {viewMode !== 'user' && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Trình phát nhúng Spotify</label>
                <SettingsSwitch checked={features['spotify']} onChange={(e) => setFeatures('spotify', !features['spotify'])} />
            </div>}
            {viewMode !== 'user' && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Sóng nền (ngốn CPU)</label>
                <SettingsSwitch checked={features['waves']} onChange={(e) => setFeatures('waves', !features['waves'])} />
            </div>}
            {showFeatures['dev'] && <div className={`${classes.settingsRow} step-settings-x `}>
                <label>Chế độ phát triển</label>
                <Input
                    disableUnderline
                    style={{
                        marginLeft: '1rem',
                        backgroundColor: 'rgb(57, 57, 61)',
                        paddingLeft: '0.5rem',
                        borderRadius: '5px',
                        paddingTop: '3px',
                        width: 50
                    }}
                    margin="dense"
                    onBlur={(e) => {
                        if (e.target.value === 'clear') { setViewMode('user'); setShowFeatures('streamto', false); setShowFeatures('dev', false); setShowFeatures('go', false); setShowFeatures('waves', false);setShowFeatures('effectfilter', false); setShowFeatures('cloud', false); setShowFeatures('rml', false); setShowFeatures('integrations', false); setShowFeatures('spotify', false); setShowFeatures('webaudio', false); setFeatures('streamto', false); setFeatures('waves', false); setFeatures('go', false); setFeatures('cloud', false);setFeatures('effectfilter', false); setFeatures('rml', false); setFeatures('dev', false); setFeatures('integrations', false); setFeatures('spotify', false); setFeatures('webaudio', false); window.localStorage.removeItem('wls-theme'); window.localStorage.setItem('BladeMod', 0); window.location.reload() }
                        if (e.target.value === 'BladeIsYeon') { setViewMode('expert'); setShowFeatures('dev', true); setShowFeatures('go', true); setShowFeatures('streamto', true); setShowFeatures('cloud', true);setShowFeatures('effectfilter', true); setShowFeatures('waves', true); setShowFeatures('rml', true); setShowFeatures('integrations', true); setShowFeatures('spotify', true); setShowFeatures('webaudio', true); setFeatures('streamto', true); setFeatures('go', true); setFeatures('waves', true); setFeatures('cloud', true); setFeatures('rml', true); setFeatures('integrations', true);setFeatures('effectfilter', true); setFeatures('spotify', true); setFeatures('webaudio', true); window.localStorage.setItem('wls-theme', "DarkBlue"); window.location.reload() }
                        if (e.target.value === 'BladeCloud') { setShowFeatures('cloud', true) }
                        if (e.target.value === 'BladeRml') { setShowFeatures('rml', true) }
                        if (e.target.value === 'BladeIntegrations') { setShowFeatures('integrations', true) }
                        if (e.target.value === 'BladeSpotify') { setShowFeatures('spotify', true) }
                        if (e.target.value === 'BladeWebaudio') { setShowFeatures('webaudio', true) }
                        if (e.target.value === 'BladeWaves') { setShowFeatures('waves', true) }
                        if (e.target.value === 'BladeStreamTo') { setShowFeatures('streamto', true) }
                        if (e.target.value === 'BladeEffectFilter') { setShowFeatures('effectfilter', true) }
                        if (e.target.value === 'BladeGo') { setShowFeatures('go', true) }
                        if (e.target.value.startsWith('theme:')) { window.localStorage.setItem('wls-theme', e.target.value.replace('theme:', '')); window.location.reload() }
                    }}
                />
            </div>}

            
        </div>
    )
}

export default UICard
