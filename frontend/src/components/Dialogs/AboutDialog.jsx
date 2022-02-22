import { useState, useEffect } from 'react';
import useStore from '../../utils/apiStore';
import { Button, Card, CardContent, CardHeader, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Divider, Link, Typography } from '@material-ui/core';
import fversion from '../../../package.json';
import GitInfo from 'react-git-info/macro';

export default function AboutDialog({ className, children, startIcon, title }) {
    const config = useStore((state) => state.config);
    const getInfo = useStore((state) => state.getInfo);
    const gitInfo = GitInfo();

    const [open, setOpen] = useState(false);
    const [bcommit, setBcommit] = useState('');
    const [bversion, setBversion] = useState('');

    const handleClickOpen = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    useEffect(async () => {
        const info = await getInfo()
        if (info && info.git_build_commit) {
            setBcommit(info.git_build_commit)
            setBversion(info.version)
        }
    }, [])

    return (
        <div>
            <Button size="small" startIcon={startIcon} variant="outlined" className={className} onClick={handleClickOpen}>
                {children}
            </Button>
            <Dialog
                open={open}
                onClose={handleClose}
                aria-labelledby="about-dialog-title"
                aria-describedby="about-dialog-description"
                
                PaperProps={{
                    style: {  margin: '0 auto' }
                }}
            >
                <DialogTitle id="about-dialog-title">
                    {"Về WiFi Led Studio"}
                </DialogTitle>
                <DialogContent>
                    
                        <div style={{ minWidth: 250 }}>
                            <Card style={{ marginBottom: '1rem' }}>
                                <CardHeader title="Hệ thống" />
                                <CardContent style={{ paddingTop: 0 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between'}}>Phiên bản cấu hình: <span>{config.configuration_version}</span> </div>    
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader title="Giao diện người dùng" />
                                <CardContent style={{ paddingTop: 0 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between'}}>Phiên bản: <span>{fversion.version}</span></div>
                                <div style={{ display: 'flex', justifyContent: 'space-between'}}>Phiên bản cấu hình: <span>{localStorage.getItem('wls-frontend')}</span></div>
                                </CardContent>
                            </Card>              
                        </div>
                    
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose} autoFocus>
                        OK
                    </Button>
                </DialogActions>
            </Dialog>
        </div>
    );
}
